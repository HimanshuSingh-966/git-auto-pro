"""GitHub Pull Request management via API."""

import requests
import webbrowser
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def _get_repo_info() -> tuple:
    """Get current user and repo name from Git remote."""
    from ..github import get_authenticated_session, get_current_user, GITHUB_API_URL, _handle_api_error
    import git
    
    session = get_authenticated_session()
    user = get_current_user()
    
    try:
        repo_obj = git.Repo(".", search_parent_directories=True)
        remotes = getattr(repo_obj, 'remotes')
        origin = getattr(remotes, 'origin')
        remote_url = origin.url
        repo_name = remote_url.split("/")[-1].replace(".git", "")
    except Exception:
        console.print("[red]✗ Could not detect repository. Use --repo option.[/red]")
        raise
    
    return session, user, repo_name, GITHUB_API_URL


def create_pull_request(
    head: str,
    base: str,
    title: str,
    body: Optional[str] = None,
    draft: bool = False,
    reviewers: Optional[List[str]] = None,
    labels: Optional[List[str]] = None,
    repo: Optional[str] = None,
) -> Dict:
    """Create a GitHub Pull Request."""
    from ..github import get_authenticated_session, get_current_user, GITHUB_API_URL, _handle_api_error
    
    session = get_authenticated_session()
    user = get_current_user()
    
    if not repo:
        _, _, repo, _ = _get_repo_info()
    
    data: Dict[str, Any] = {
        "title": title,
        "head": head,
        "base": base,
        "draft": draft,
    }
    if body:
        data["body"] = body
    
    try:
        response = session.post(
            f"{GITHUB_API_URL}/repos/{user['login']}/{repo}/pulls",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        pr_data = response.json()
        
        console.print(f"[green]✓ PR #{pr_data['number']} created: {pr_data['html_url']}[/green]")
        
        # Add reviewers if specified
        if reviewers:
            try:
                session.post(
                    f"{GITHUB_API_URL}/repos/{user['login']}/{repo}/pulls/{pr_data['number']}/requested_reviewers",
                    json={"reviewers": reviewers},
                    timeout=10
                )
                console.print(f"[green]✓ Reviewers requested: {', '.join(reviewers)}[/green]")
            except Exception:
                console.print("[yellow]⚠ Could not add reviewers[/yellow]")
        
        # Add labels if specified
        if labels:
            try:
                session.post(
                    f"{GITHUB_API_URL}/repos/{user['login']}/{repo}/issues/{pr_data['number']}/labels",
                    json={"labels": labels},
                    timeout=10
                )
                console.print(f"[green]✓ Labels added: {', '.join(labels)}[/green]")
            except Exception:
                console.print("[yellow]⚠ Could not add labels[/yellow]")
        
        return pr_data
        
    except (requests.ConnectionError, requests.Timeout) as e:
        _handle_api_error("Create PR", e)
        raise
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            console.print("[red]✗ PR already exists or invalid branch[/red]")
        else:
            _handle_api_error("Create PR", e)
        raise


def list_pull_requests(state: str = "open", repo: Optional[str] = None) -> List[Dict]:
    """List pull requests for the repository."""
    from ..github import get_authenticated_session, get_current_user, GITHUB_API_URL, _handle_api_error
    
    session = get_authenticated_session()
    user = get_current_user()
    
    if not repo:
        _, _, repo, _ = _get_repo_info()
    
    try:
        response = session.get(
            f"{GITHUB_API_URL}/repos/{user['login']}/{repo}/pulls",
            params={"state": state, "per_page": 30},
            timeout=10
        )
        response.raise_for_status()
        prs = response.json()
        
        if not prs:
            console.print(f"[yellow]No {state} pull requests found[/yellow]")
            return []
        
        table = Table(title=f"{state.capitalize()} Pull Requests", show_header=True)
        table.add_column("#", style="yellow", width=6)
        table.add_column("Title", style="cyan")
        table.add_column("Branch", style="green", width=25)
        table.add_column("Author", style="magenta", width=15)
        
        for pr in prs:
            table.add_row(
                str(pr["number"]),
                pr["title"][:50],
                pr["head"]["ref"],
                pr["user"]["login"]
            )
        
        console.print(table)
        return prs
        
    except (requests.ConnectionError, requests.Timeout) as e:
        _handle_api_error("List PRs", e)
        return []
    except Exception as e:
        console.print(f"[red]✗ Failed to list PRs: {e}[/red]")
        return []


def merge_pull_request(
    number: int,
    method: str = "merge",
    repo: Optional[str] = None
) -> bool:
    """Merge a pull request by number."""
    from ..github import get_authenticated_session, get_current_user, GITHUB_API_URL, _handle_api_error
    
    session = get_authenticated_session()
    user = get_current_user()
    
    if not repo:
        _, _, repo, _ = _get_repo_info()
    
    valid_methods = ("merge", "squash", "rebase")
    if method not in valid_methods:
        console.print(f"[red]✗ Invalid merge method. Use: {', '.join(valid_methods)}[/red]")
        return False
    
    try:
        response = session.put(
            f"{GITHUB_API_URL}/repos/{user['login']}/{repo}/pulls/{number}/merge",
            json={"merge_method": method},
            timeout=10
        )
        response.raise_for_status()
        
        console.print(f"[green]✓ PR #{number} merged ({method})[/green]")
        return True
        
    except (requests.ConnectionError, requests.Timeout) as e:
        _handle_api_error("Merge PR", e)
        return False
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 405:
            console.print(f"[red]✗ PR #{number} cannot be merged — check for conflicts[/red]")
        elif e.response.status_code == 409:
            console.print(f"[red]✗ PR #{number} head branch was modified — review required[/red]")
        else:
            _handle_api_error("Merge PR", e)
        return False


def get_pull_request(number: int, repo: Optional[str] = None) -> Optional[Dict]:
    """Get details of a specific pull request."""
    from ..github import get_authenticated_session, get_current_user, GITHUB_API_URL, _handle_api_error
    
    session = get_authenticated_session()
    user = get_current_user()
    
    if not repo:
        _, _, repo, _ = _get_repo_info()
    
    try:
        response = session.get(
            f"{GITHUB_API_URL}/repos/{user['login']}/{repo}/pulls/{number}",
            timeout=10
        )
        response.raise_for_status()
        pr = response.json()
        
        info = f"""[bold cyan]PR #{pr['number']}[/bold cyan]
[bold]Title:[/bold] {pr['title']}
[bold]State:[/bold] {pr['state']}
[bold]Author:[/bold] {pr['user']['login']}
[bold]Branch:[/bold] {pr['head']['ref']} → {pr['base']['ref']}
[bold]Created:[/bold] {pr['created_at'][:10]}
[bold]URL:[/bold] {pr['html_url']}

[bold]Description:[/bold]
{pr.get('body', 'No description provided') or 'No description provided'}
"""
        
        console.print(Panel(info, border_style="cyan"))
        return pr
        
    except (requests.ConnectionError, requests.Timeout) as e:
        _handle_api_error("Get PR", e)
        return None
    except Exception as e:
        console.print(f"[red]✗ Failed to get PR: {e}[/red]")
        return None


def review_pr_in_browser(number: int, repo: Optional[str] = None) -> None:
    """Open a PR in the browser for review."""
    from ..github import get_authenticated_session, get_current_user, GITHUB_API_URL
    
    session = get_authenticated_session()
    user = get_current_user()
    
    if not repo:
        _, _, repo, _ = _get_repo_info()
    
    url = f"https://github.com/{user['login']}/{repo}/pull/{number}"
    console.print(f"[cyan]Opening PR #{number} in browser...[/cyan]")
    webbrowser.open(url)
