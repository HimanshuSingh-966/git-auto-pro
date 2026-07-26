"""GitHub Pull Request management via API."""

import requests
import webbrowser
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


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
    from ..github import (
        get_authenticated_session,
        resolve_repo_ref,
        GITHUB_API_URL,
        _handle_api_error,
    )

    session = get_authenticated_session()

    try:
        owner, repo_name = resolve_repo_ref(repo)
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise

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
            f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/pulls",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        pr_data = response.json()

        console.print(f"[green]✓ PR #{pr_data['number']} created: {pr_data['html_url']}[/green]")

        # Add reviewers if specified — report the real outcome, don't claim
        # success when the API rejected the request.
        if reviewers:
            try:
                rv = session.post(
                    f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/pulls/{pr_data['number']}/requested_reviewers",
                    json={"reviewers": reviewers},
                    timeout=10
                )
                rv.raise_for_status()
                console.print(f"[green]✓ Reviewers requested: {', '.join(reviewers)}[/green]")
            except requests.exceptions.HTTPError as e:
                status = getattr(e.response, 'status_code', 'unknown')
                console.print(f"[yellow]⚠ Could not add reviewers (HTTP {status})[/yellow]")
            except (requests.ConnectionError, requests.Timeout):
                console.print("[yellow]⚠ Could not add reviewers — network error[/yellow]")

        # Add labels if specified — same accurate reporting.
        if labels:
            try:
                lb = session.post(
                    f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/issues/{pr_data['number']}/labels",
                    json={"labels": labels},
                    timeout=10
                )
                lb.raise_for_status()
                console.print(f"[green]✓ Labels added: {', '.join(labels)}[/green]")
            except requests.exceptions.HTTPError as e:
                status = getattr(e.response, 'status_code', 'unknown')
                console.print(f"[yellow]⚠ Could not add labels (HTTP {status})[/yellow]")
            except (requests.ConnectionError, requests.Timeout):
                console.print("[yellow]⚠ Could not add labels — network error[/yellow]")

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
    from ..github import (
        get_authenticated_session,
        resolve_repo_ref,
        GITHUB_API_URL,
        _handle_api_error,
    )

    session = get_authenticated_session()

    try:
        owner, repo_name = resolve_repo_ref(repo)
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        return []

    try:
        response = session.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/pulls",
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
    from ..github import (
        get_authenticated_session,
        resolve_repo_ref,
        GITHUB_API_URL,
        _handle_api_error,
    )

    session = get_authenticated_session()

    try:
        owner, repo_name = resolve_repo_ref(repo)
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        return False

    valid_methods = ("merge", "squash", "rebase")
    if method not in valid_methods:
        console.print(f"[red]✗ Invalid merge method. Use: {', '.join(valid_methods)}[/red]")
        return False

    try:
        response = session.put(
            f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/pulls/{number}/merge",
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
        status = getattr(e.response, 'status_code', 'unknown')
        if status == 405:
            # 405 = merge not permitted: failing/pending required checks,
            # missing reviews, draft, or branch protection rules.
            console.print(f"[red]✗ PR #{number} is not mergeable[/red]")
            console.print("[yellow]→ Pending/failed required checks, missing reviews, draft, or branch protection may block the merge.[/yellow]")
        elif status == 409:
            # 409 = head/base conflict or the head branch changed mid-merge.
            console.print(f"[red]✗ PR #{number} has merge conflicts or the head branch changed[/red]")
            console.print("[yellow]→ Resolve conflicts or re-review, then try again.[/yellow]")
        else:
            _handle_api_error("Merge PR", e)
        return False


def get_pull_request(number: int, repo: Optional[str] = None) -> Optional[Dict]:
    """Get details of a specific pull request."""
    from ..github import (
        get_authenticated_session,
        resolve_repo_ref,
        GITHUB_API_URL,
        _handle_api_error,
    )

    session = get_authenticated_session()

    try:
        owner, repo_name = resolve_repo_ref(repo)
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        return None

    try:
        response = session.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/pulls/{number}",
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
    from ..github import get_authenticated_session, resolve_repo_ref

    session = get_authenticated_session()

    try:
        owner, repo_name = resolve_repo_ref(repo)
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        return

    url = f"https://github.com/{owner}/{repo_name}/pull/{number}"
    console.print(f"[cyan]Opening PR #{number} in browser...[/cyan]")
    webbrowser.open(url)
