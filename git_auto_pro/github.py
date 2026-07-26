"""GitHub API integration module."""

import requests
import keyring
from pathlib import Path
import json
from typing import Optional, List, Dict, Tuple
from rich.console import Console
from rich.prompt import Prompt, Confirm
import questionary

console = Console()

SERVICE_NAME = "git-auto-pro"
TOKEN_KEY = "github-token"
GITHUB_API_URL = "https://api.github.com"


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
        status = getattr(error.response, 'status_code', 'unknown')
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
            except Exception:
                pass
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
            except Exception:
                pass
            console.print("[green]✓ Token stored in file[/green]")


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
    """Get authenticated requests session."""
    token = get_stored_token()
    if not token:
        console.print("[red]✗ Not authenticated. Run 'git-auto login' first.[/red]")
        raise ValueError("Not authenticated")
    
    session = requests.Session()
    session.headers.update(_auth_headers(token))
    return session


def get_current_user() -> Dict:
    """Get current authenticated user information."""
    try:
        session = get_authenticated_session()
        response = session.get(f"{GITHUB_API_URL}/user", timeout=10)
        response.raise_for_status()
        return response.json()
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
                f"{GITHUB_API_URL}/repos/{user['login']}/{name}/topics",
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
            f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/collaborators/{username}",
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
            f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/branches/{branch}/protection",
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

    if not _use_file_storage():
        try:
            keyring.delete_password(SERVICE_NAME, TOKEN_KEY)
            console.print("[green]✓ Token cleared from keyring[/green]")
            return
        except Exception:
            pass
    

    if TOKEN_FILE.exists():
        try:
            TOKEN_FILE.unlink()
            console.print("[green]✓ Token cleared from file[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to clear token: {e}[/red]")