"""GitHub API integration module."""

import re
import requests
import keyring
from pathlib import Path
from urllib.parse import quote
from datetime import datetime, timezone
import json
from typing import Optional, List, Dict, Tuple, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm
import questionary

console = Console()

SERVICE_NAME = "git-auto-pro"
TOKEN_KEY = "github-token"
GITHUB_API_URL = "https://api.github.com"

# Module-level caches so we don't re-fetch the token/session or hit
# GET /user on every single GitHub operation. Invalidated by clear_auth_cache()
# on login / logout / token changes. The CLI is single-threaded; these are
# plain globals.
_session_cache: Optional[requests.Session] = None
_current_user_cache: Optional[Dict] = None


def check_api_connectivity() -> bool:
    """Check if GitHub API is reachable."""
    try:
        response = requests.head(GITHUB_API_URL, timeout=5)
        return response.status_code < 500
    except (requests.ConnectionError, requests.Timeout):
        return False
    except Exception:
        return False


def _handle_api_error(operation: str, error: Exception) -> None:
    """Handle API errors with user-friendly messages."""
    if isinstance(error, (requests.ConnectionError, requests.Timeout)):
        console.print(f"[red]✗ {operation}: Cannot reach GitHub API — check your internet connection.[/red]")
        console.print("[yellow]→ Local Git operations still work. GitHub features require connectivity.[/yellow]")
    elif isinstance(error, requests.exceptions.HTTPError):
        resp = getattr(error, 'response', None)
        status = getattr(resp, 'status_code', 'unknown') if resp is not None else 'unknown'
        if resp is not None and _is_rate_limited(resp):
            console.print(
                f"[red]✗ {operation}: GitHub API rate limit hit (HTTP {status}).[/red]"
            )
            console.print(f"[yellow]→ {_rate_limit_hint(resp)}[/yellow]")
        else:
            console.print(f"[red]✗ {operation}: GitHub API returned HTTP {status}[/red]")
    else:
        console.print(f"[red]✗ {operation}: {error}[/red]")


def _auth_headers(token: str) -> Dict[str, str]:
    """Build standard auth headers for a GitHub API request."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _api_url(*parts: str) -> str:
    """Build a GitHub API URL, URL-encoding each path segment.

    e.g. _api_url("repos", owner, repo, "issues") -> ".../repos/<owner>/<repo>/issues"
    Owner/repo/username/branch may contain characters that are unsafe in a URL
    path (e.g. '#', '?', spaces); quoting prevents both broken requests and
    path-injection. Slashes within a segment are encoded too, so a segment
    can't escape its position.
    """
    return GITHUB_API_URL + "/" + "/".join(quote(str(p), safe="") for p in parts)


def _is_rate_limited(response: requests.Response) -> bool:
    """True if the response indicates the API rate limit was hit (429, or a
    403 with X-RateLimit-Remaining: 0)."""
    status = getattr(response, "status_code", None)
    if status == 429:
        return True
    if status == 403:
        remaining = response.headers.get("X-RateLimit-Remaining")
        if remaining is not None:
            try:
                return int(remaining) <= 0
            except (ValueError, TypeError):
                return False
    return False


def _rate_limit_hint(response: requests.Response) -> str:
    """A human-readable hint about when the rate limit resets / how long to wait."""
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            secs = int(retry_after)
            return f"Retry in ~{secs}s (Retry-After)."
        except (ValueError, TypeError):
            pass
    reset = response.headers.get("X-RateLimit-Reset")
    if reset:
        try:
            reset_dt = datetime.fromtimestamp(int(reset), tz=timezone.utc)
            return f"Resets at {reset_dt:%Y-%m-%d %H:%M UTC}."
        except (ValueError, TypeError, OSError):
            pass
    return "Wait and try again later."


def _check_rate_limit(response: requests.Response, operation: str) -> None:
    """Print a proactive warning when the rate limit is low or exhausted on a
    *successful* response. Raises nothing."""
    remaining = response.headers.get("X-RateLimit-Remaining")
    # Real HTTP headers are strings; guard against non-string values (e.g.
    # mocks) rather than acting on them.
    if not isinstance(remaining, str):
        return
    try:
        remaining_int = int(remaining)
    except (ValueError, TypeError):
        return
    if remaining_int <= 0:
        console.print(f"[yellow]⚠ {operation}: rate limit now exhausted. {_rate_limit_hint(response)}[/yellow]")
    elif remaining_int <= 5:
        console.print(f"[yellow]⚠ GitHub API rate limit low: {remaining_int} requests left.[/yellow]")


_LINK_NEXT_RE = re.compile(r'<([^>]+)>\s*;\s*rel="next"')


def _next_link(link_header: str) -> Optional[str]:
    """Extract the rel="next" URL from a GitHub Link header, or None."""
    if not isinstance(link_header, str) or not link_header:
        return None
    match = _LINK_NEXT_RE.search(link_header)
    return match.group(1) if match else None


def _paginated_get(
    session: requests.Session,
    url: str,
    params: Optional[Dict[str, Any]],
    limit: int,
    operation: str,
) -> List[Dict]:
    """GET a paginated GitHub list endpoint, following the Link rel="next"
    header, until `limit` items are collected or the pages run out.

    GitHub caps per_page at 100, so a single request silently truncated large
    lists before. The first request uses `params` (with per_page set); later
    requests use the next-page URL verbatim (it already carries query params).
    """
    items: List[Dict] = []
    per_page = min(max(int(limit), 1), 100)
    first_params = dict(params or {})
    first_params["per_page"] = per_page

    next_url: Optional[str] = url
    use_params: Optional[Dict[str, Any]] = first_params
    while next_url:
        response = session.get(next_url, params=use_params, timeout=10)
        response.raise_for_status()
        _check_rate_limit(response, operation)
        batch = response.json() or []
        if not batch:
            break
        items.extend(batch)
        if len(items) >= limit:
            break
        next_url = _next_link(response.headers.get("Link", ""))
        use_params = None  # next URL already contains its own query string
    return items[:limit]


def clear_auth_cache() -> None:
    """Clear the cached authenticated session and current-user dict.

    Called after login/logout/token changes so the next call rebuilds them
    with the (possibly new) token.
    """
    global _session_cache, _current_user_cache
    _session_cache = None
    _current_user_cache = None


def parse_remote_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse (owner, repo) from a GitHub remote URL.

    Supports HTTPS (https://github.com/owner/repo[.git]), scp-like SSH
    (git@github.com:owner/repo[.git]), and ssh:// / git:// forms.
    Returns (owner, repo) with any trailing '.git' stripped, or
    (None, None) if the URL cannot be parsed.
    """
    url = url.strip()
    if url.endswith(".git"):
        url = url[:-4]
    url = url.rstrip("/")

    # scp-like form: git@github.com:owner/repo  (no "://", but has a ":")
    if "://" not in url and ":" in url:
        path = url.split(":", 1)[1]
    elif "://" in url:
        # strip scheme + userinfo/host, keep the owner/repo path
        rest = url.split("://", 1)[1]
        path = rest.split("/", 1)[1] if "/" in rest else ""
    else:
        path = url

    parts = [p for p in path.split("/") if p] if path else []
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    if len(parts) == 1:
        return None, parts[-1]
    return None, None


def detect_repo_from_remote() -> Tuple[str, str]:
    """Detect (owner, repo) from the local git origin remote.

    Raises RuntimeError with a user-friendly message if not a git repo,
    no origin remote, or the URL can't be parsed.
    """
    import git
    try:
        repo_obj = git.Repo(".", search_parent_directories=True)
    except Exception as e:
        raise RuntimeError(
            "Not a git repository. Use --repo owner/name to specify one."
        ) from e
    remotes = getattr(repo_obj, "remotes", None)
    if not remotes or not hasattr(remotes, "origin"):
        raise RuntimeError(
            "No 'origin' remote configured. Use --repo owner/name to specify one."
        )
    origin = remotes.origin
    try:
        remote_url = origin.url
    except Exception as e:
        raise RuntimeError(
            "No URL configured for 'origin' remote. Use --repo owner/name to specify one."
        ) from e
    owner, name = parse_remote_url(remote_url)
    if not owner or not name:
        raise RuntimeError(
            f"Could not parse GitHub owner/repo from remote URL: {remote_url!r}. "
            "Use --repo owner/name to specify one."
        )
    return owner, name


def resolve_repo_ref(repo: Optional[str] = None) -> Tuple[str, str]:
    """Resolve (owner, repo_name) for a GitHub API call.

    - repo="owner/name"  -> ("owner", "name")
    - repo="name" (bare) -> (authenticated_user, "name")   [legacy behavior]
    - repo=None          -> detect owner+name from the local origin remote
    """
    if repo:
        if "/" in repo:
            owner, name = repo.split("/", 1)
            return owner.strip(), name.strip()
        user = get_current_user()
        return user["login"], repo.strip()
    return detect_repo_from_remote()


TOKEN_FILE = Path.home() / ".git-auto-token.json"


def _use_file_storage() -> bool:
    """Check if we should use file-based storage."""
    try:

        keyring.get_keyring()

        test_service = "git-auto-test"
        try:
            keyring.set_password(test_service, "test", "test")
            keyring.delete_password(test_service, "test")
            return False
        except Exception:
            return True
    except Exception:
        return True


def get_stored_token() -> Optional[str]:
    """Retrieve stored GitHub token from keyring or file."""

    if not _use_file_storage():
        try:
            token = keyring.get_password(SERVICE_NAME, TOKEN_KEY)
            if token:
                return token
        except Exception as e:
            console.print(f"[yellow]Warning: Keyring access failed: {e}[/yellow]")
    

    if TOKEN_FILE.exists():
        try:
            data = json.loads(TOKEN_FILE.read_text())
            return data.get("token")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read token file: {e}[/yellow]")
    
    return None


def store_token(token: str) -> None:
    """Store GitHub token in keyring or file."""
    use_file = _use_file_storage()

    if use_file:

        console.print("[yellow]⚠️  Keyring not available, using file-based storage[/yellow]")
        console.print(f"[dim]Token will be stored in: {TOKEN_FILE}[/dim]")

        try:
            TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {"token": token}
            TOKEN_FILE.write_text(json.dumps(data, indent=2))

            try:
                TOKEN_FILE.chmod(0o600)
            except OSError as e:
                # Permissions couldn't be tightened — the plaintext token may
                # be readable by other users. Don't swallow this silently.
                console.print(f"[yellow]⚠ Could not chmod token file to 0o600: {e}[/yellow]")
                console.print("[yellow]  The stored token may be readable by other users on this system.[/yellow]")
            console.print("[green]✓ Token stored securely in file[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to store token: {e}[/red]")
            raise
    else:

        try:
            keyring.set_password(SERVICE_NAME, TOKEN_KEY, token)
            console.print("[green]✓ Token stored securely in keyring[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to store token in keyring: {e}[/red]")

            console.print("[yellow]Falling back to file storage...[/yellow]")
            TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {"token": token}
            TOKEN_FILE.write_text(json.dumps(data, indent=2))
            try:
                TOKEN_FILE.chmod(0o600)
            except OSError as e:
                console.print(f"[yellow]⚠ Could not chmod token file to 0o600: {e}[/yellow]")
                console.print("[yellow]  The stored token may be readable by other users on this system.[/yellow]")
            console.print("[green]✓ Token stored in file[/green]")

    # A new token means any cached session/user are stale.
    clear_auth_cache()


def validate_token(token: str) -> bool:
    """Validate GitHub token using API."""
    headers = _auth_headers(token)

    try:
        response = requests.get(f"{GITHUB_API_URL}/user", headers=headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            console.print(f"[green]✓ Authenticated as: {user_data['login']}[/green]")
            return True
        else:
            console.print(f"[red]✗ Invalid token: {response.status_code}[/red]")
            return False
    except (requests.ConnectionError, requests.Timeout):
        console.print("[red]✗ Cannot reach GitHub API — check your internet connection.[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ Validation failed: {e}[/red]")
        return False


def login_github(token: Optional[str] = None) -> None:
    """Login to GitHub using Personal Access Token."""
    console.print("[bold cyan]🔐 GitHub Authentication[/bold cyan]\n")
    
    if not token:
        console.print("To create a token, visit: https://github.com/settings/tokens")
        console.print("Required scopes: repo, workflow, admin:org\n")
        token = Prompt.ask("Enter your GitHub Personal Access Token", password=True)
    
    if not token:
        console.print("[red]✗ No token provided[/red]")
        return
    
    if validate_token(token):
        store_token(token)
        console.print("[bold green]✓ Login successful![/bold green]")
    else:
        console.print("[red]✗ Login failed[/red]")


def get_authenticated_session() -> requests.Session:
    """Get authenticated requests session (cached per process)."""
    global _session_cache
    if _session_cache is not None:
        return _session_cache
    token = get_stored_token()
    if not token:
        console.print("[red]✗ Not authenticated. Run 'git-auto login' first.[/red]")
        raise ValueError("Not authenticated")

    session = requests.Session()
    session.headers.update(_auth_headers(token))
    _session_cache = session
    return session


def get_current_user() -> Dict:
    """Get current authenticated user information (cached per process)."""
    global _current_user_cache
    if _current_user_cache is not None:
        return _current_user_cache
    try:
        session = get_authenticated_session()
        response = session.get(f"{GITHUB_API_URL}/user", timeout=10)
        response.raise_for_status()
        _current_user_cache = response.json()
        return _current_user_cache
    except (requests.ConnectionError, requests.Timeout) as e:
        _handle_api_error("Get user info", e)
        raise
    except Exception as e:
        _handle_api_error("Get user info", e)
        raise


def create_github_repo(
    name: str,
    private: bool = False,
    description: Optional[str] = None,
    homepage: Optional[str] = None,
    topics: Optional[List[str]] = None,
    auto_init: bool = False,
) -> Dict:
    """Create a new GitHub repository."""
    console.print(f"[bold cyan]📦 Creating repository: {name}[/bold cyan]\n")
    
    session = get_authenticated_session()
    user = get_current_user()
    
    data = {
        "name": name,
        "private": private,
        "auto_init": auto_init,
    }
    
    if description:
        data["description"] = description
    if homepage:
        data["homepage"] = homepage
    
    try:
        response = session.post(f"{GITHUB_API_URL}/user/repos", json=data, timeout=10)
        response.raise_for_status()
        repo_data = response.json()
        
        console.print(f"[green]✓ Repository created: {repo_data['html_url']}[/green]")
        

        if topics:
            topics_response = session.put(
                _api_url("repos", user["login"], name, "topics"),
                json={"names": topics},
                timeout=10
            )
            if topics_response.status_code == 200:
                console.print(f"[green]✓ Topics added: {', '.join(topics)}[/green]")
            else:
                console.print(
                    f"[yellow]⚠ Topics not added (HTTP {topics_response.status_code})[/yellow]"
                )
        
        return repo_data
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            console.print(f"[red]✗ Repository '{name}' already exists[/red]")
        else:
            _handle_api_error("Create repository", e)
        raise
    except (requests.ConnectionError, requests.Timeout) as e:
        _handle_api_error("Create repository", e)
        raise


def add_collaborator(
    username: str,
    repo: Optional[str] = None,
    permission: str = "push"
) -> None:
    """Add a collaborator to a repository."""
    session = get_authenticated_session()

    try:
        owner, repo_name = resolve_repo_ref(repo)
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        return

    console.print(f"[cyan]Adding {username} as collaborator to {owner}/{repo_name}...[/cyan]")

    try:
        response = session.put(
            _api_url("repos", owner, repo_name, "collaborators", username),
            json={"permission": permission},
            timeout=10
        )
        response.raise_for_status()
        console.print(f"[green]✓ Collaborator added: {username} ({permission})[/green]")
    except (requests.ConnectionError, requests.Timeout) as e:
        _handle_api_error("Add collaborator", e)
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', 'unknown')
        if status == 404:
            console.print(f"[red]✗ Repository '{owner}/{repo_name}' not found (404). Check --repo.[/red]")
        else:
            _handle_api_error("Add collaborator", e)
    except Exception as e:
        console.print(f"[red]✗ Failed to add collaborator: {e}[/red]")


def protect_branch(
    branch: str = "main",
    repo: Optional[str] = None
) -> None:
    """Setup branch protection rules."""
    session = get_authenticated_session()

    try:
        owner, repo_name = resolve_repo_ref(repo)
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        return

    console.print(f"[cyan]Setting up protection for branch '{branch}' on {owner}/{repo_name}...[/cyan]")

    protection_data = {
        "required_status_checks": None,
        "enforce_admins": False,
        "required_pull_request_reviews": {
            "dismissal_restrictions": {},
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 1
        },
        "restrictions": None
    }

    try:
        response = session.put(
            _api_url("repos", owner, repo_name, "branches", branch, "protection"),
            json=protection_data,
            timeout=10
        )
        response.raise_for_status()
        console.print(f"[green]✓ Branch protection enabled for '{branch}'[/green]")
    except (requests.ConnectionError, requests.Timeout) as e:
        _handle_api_error("Protect branch", e)
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', 'unknown')
        if status == 404:
            console.print(f"[red]✗ Repository '{owner}/{repo_name}' or branch '{branch}' not found (404).[/red]")
        else:
            _handle_api_error("Protect branch", e)
    except Exception as e:
        console.print(f"[red]✗ Failed to protect branch: {e}[/red]")


def clear_stored_token() -> None:
    """Clear stored token (for logout/reset)."""

    cleared = False
    keyring_failed = False

    if not _use_file_storage():
        try:
            keyring.delete_password(SERVICE_NAME, TOKEN_KEY)
            console.print("[green]✓ Token cleared from keyring[/green]")
            cleared = True
        except Exception:
            # Keyring delete failed — don't swallow silently; the token may
            # still be stored. Fall through to the file path, then warn.
            keyring_failed = True

    if TOKEN_FILE.exists():
        try:
            TOKEN_FILE.unlink()
            console.print("[green]✓ Token cleared from file[/green]")
            cleared = True
        except Exception as e:
            console.print(f"[red]✗ Failed to clear token file: {e}[/red]")

    if keyring_failed and not TOKEN_FILE.exists():
        console.print(
            "[yellow]⚠ Could not remove the token from the keyring — it may still be stored.[/yellow]"
        )
        console.print("[yellow]  Remove it manually from your OS keyring/credential manager.[/yellow]")
    elif not cleared:
        console.print("[yellow]No stored token found to clear.[/yellow]")

    # Drop any cached session/user built from the now-cleared token.
    clear_auth_cache()