"""GitHub issues management functions."""

from typing import Optional, List, Dict, Any
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import git

console = Console()


def create_issue(
    title: str,
    body: Optional[str] = None,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    repo: Optional[str] = None
) -> Dict:
    """Create a new GitHub issue."""
    from .github import get_authenticated_session, resolve_repo_ref, _api_url

    console.print("[bold cyan]📝 Creating GitHub Issue[/bold cyan]\n")

    session = get_authenticated_session()

    try:
        owner, repo_name = resolve_repo_ref(repo)
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        return {}

    data: Dict[str, Any] = {"title": title}

    if body:
        data["body"] = body
    if labels:
        data["labels"] = labels
    if assignees:
        data["assignees"] = assignees

    try:
        response = session.post(
            _api_url("repos", owner, repo_name, "issues"),
            json=data,
            timeout=10
        )
        response.raise_for_status()
        issue_data = response.json()

        console.print(f"[green]✓ Issue created: #{issue_data['number']}[/green]")
        console.print(f"[cyan]URL: {issue_data['html_url']}[/cyan]")

        return issue_data

    except (requests.ConnectionError, requests.Timeout):
        console.print("[red]✗ Cannot reach GitHub API — check your internet connection.[/red]")
        return {}
    except requests.exceptions.HTTPError as e:
        # Consistent contract with the other issue operations: return an empty
        # result on failure rather than raising to the CLI layer.
        console.print(f"[red]✗ Failed to create issue: {e}[/red]")
        return {}


def list_issues(
    state: str = "open",
    labels: Optional[str] = None,
    assignee: Optional[str] = None,
    repo: Optional[str] = None,
    limit: int = 30,
    json_output: bool = False,
) -> List[Dict]:
    """List GitHub issues."""
    from .github import (
        get_authenticated_session,
        resolve_repo_ref,
        _api_url,
        _paginated_get,
    )

    if not json_output:
        console.print(f"[bold cyan]📋 Listing {state.capitalize()} Issues[/bold cyan]\n")

    session = get_authenticated_session()

    try:
        owner, repo_name = resolve_repo_ref(repo)
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        return []

    params: Dict[str, Any] = {"state": state}
    if labels:
        params["labels"] = labels
    if assignee:
        params["assignee"] = assignee

    try:
        # Paginate via the Link rel="next" header so large repos aren't
        # silently truncated at GitHub's 100-per-page ceiling.
        issues = _paginated_get(
            session,
            _api_url("repos", owner, repo_name, "issues"),
            params,
            limit,
            "List issues",
        )

        if not json_output:
            if not issues:
                console.print(f"[yellow]No {state} issues found[/yellow]")
                return []

            table = Table(show_header=True)
            table.add_column("#", style="yellow", width=6)
            table.add_column("Title", style="cyan")
            table.add_column("State", style="green", width=8)
            table.add_column("Labels", style="magenta", width=20)

            for issue in issues:
                labels_str = ", ".join([label["name"] for label in issue.get("labels", [])])
                table.add_row(
                    str(issue["number"]),
                    issue["title"][:50],
                    issue["state"],
                    labels_str[:20]
                )

            console.print(table)
            console.print(f"\n[dim]Showing {len(issues)} issues[/dim]")

        return issues

    except (requests.ConnectionError, requests.Timeout):
        console.print("[red]✗ Cannot reach GitHub API — check your internet connection.[/red]")
        return []
    except requests.exceptions.HTTPError as e:
        console.print(f"[red]✗ Failed to list issues: {e}[/red]")
        return []


def get_issue(number: int, repo: Optional[str] = None, json_output: bool = False) -> Optional[Dict]:
    """Get details of a specific issue."""
    from .github import get_authenticated_session, resolve_repo_ref, _api_url

    session = get_authenticated_session()

    try:
        owner, repo_name = resolve_repo_ref(repo)
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        return None

    try:
        response = session.get(
            _api_url("repos", owner, repo_name, "issues", number),
            timeout=10
        )
        response.raise_for_status()
        issue = response.json()

        if not json_output:
            labels_str = ", ".join([label["name"] for label in issue.get("labels", [])])
            assignees_str = ", ".join([assignee["login"] for assignee in issue.get("assignees", [])])

            info = f"""[bold cyan]Issue #{issue['number']}[/bold cyan]
[bold]Title:[/bold] {issue['title']}
[bold]State:[/bold] {issue['state']}
[bold]Author:[/bold] {issue['user']['login']}
[bold]Created:[/bold] {issue['created_at'][:10]}
[bold]Labels:[/bold] {labels_str or 'None'}
[bold]Assignees:[/bold] {assignees_str or 'None'}
[bold]URL:[/bold] {issue['html_url']}

[bold]Description:[/bold]
{issue.get('body', 'No description provided')}
"""

            console.print(Panel(info, border_style="cyan"))

        return issue

    except (requests.ConnectionError, requests.Timeout):
        console.print("[red]✗ Cannot reach GitHub API — check your internet connection.[/red]")
        return None
    except requests.exceptions.HTTPError as e:
        console.print(f"[red]✗ Failed to get issue: {e}[/red]")
        return None


def close_issue(
    number: int,
    comment: Optional[str] = None,
    repo: Optional[str] = None
) -> bool:
    """Close a GitHub issue."""
    from .github import get_authenticated_session, resolve_repo_ref, _api_url

    console.print(f"[bold cyan]🔒 Closing Issue #{number}[/bold cyan]\n")

    session = get_authenticated_session()

    try:
        owner, repo_name = resolve_repo_ref(repo)
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        return False

    try:
        # Post the closing comment best-effort: a failure here must not abort
        # the actual close (PATCH) below.
        if comment:
            try:
                session.post(
                    _api_url("repos", owner, repo_name, "issues", number, "comments"),
                    json={"body": comment},
                    timeout=10
                )
            except (requests.ConnectionError, requests.Timeout):
                console.print("[yellow]⚠ Could not post closing comment — network error[/yellow]")

        response = session.patch(
            _api_url("repos", owner, repo_name, "issues", number),
            json={"state": "closed"},
            timeout=10
        )
        response.raise_for_status()

        console.print(f"[green]✓ Issue #{number} closed successfully[/green]")
        return True

    except (requests.ConnectionError, requests.Timeout):
        console.print("[red]✗ Cannot reach GitHub API — check your internet connection.[/red]")
        return False
    except requests.exceptions.HTTPError as e:
        console.print(f"[red]✗ Failed to close issue: {e}[/red]")
        return False


def update_issue(
    number: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
    labels: Optional[List[str]] = None,
    repo: Optional[str] = None
) -> Optional[Dict]:
    """Update a GitHub issue."""
    from .github import get_authenticated_session, resolve_repo_ref, _api_url

    console.print(f"[bold cyan]✏️  Updating Issue #{number}[/bold cyan]\n")

    session = get_authenticated_session()

    try:
        owner, repo_name = resolve_repo_ref(repo)
    except RuntimeError as e:
        console.print(f"[red]✗ {e}[/red]")
        return None

    data = {}
    if title:
        data["title"] = title
    if body:
        data["body"] = body
    if state:
        data["state"] = state
    if labels:
        data["labels"] = labels

    if not data:
        console.print("[yellow]No updates specified[/yellow]")
        return None

    try:
        response = session.patch(
            _api_url("repos", owner, repo_name, "issues", number),
            json=data,
            timeout=10
        )
        response.raise_for_status()
        issue = response.json()

        console.print(f"[green]✓ Issue #{number} updated successfully[/green]")
        return issue

    except (requests.ConnectionError, requests.Timeout):
        console.print("[red]✗ Cannot reach GitHub API — check your internet connection.[/red]")
        return None
    except requests.exceptions.HTTPError as e:
        console.print(f"[red]✗ Failed to update issue: {e}[/red]")
        return None
