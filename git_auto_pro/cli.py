"""Main CLI interface using Typer."""

import typer
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import questionary

# Import submodules
from .github import (
    login_github,
    create_github_repo,
    add_collaborator,
    protect_branch,
)
from .github_issues import (
    create_issue,
    list_issues,
    get_issue,
    close_issue,
    update_issue,
)
from .git_commands import (
    git_init,
    git_add,
    git_commit,
    git_push,
    git_pull,
    git_status,
    git_log,
    git_branch,
    git_switch,
    git_delete_branch,
    git_stash,
    git_stash_apply,
    git_merge,
    git_clone,
    git_stats,
    git_undo,
)
from .config import (
    get_config,
    set_config,
    list_config,
    reset_config,
    load_config,
)
from .scaffolding.project import create_new_project
from .scaffolding.readme import generate_readme
from .scaffolding.license import generate_license
from .scaffolding.gitignore import generate_gitignore
from .scaffolding.templates import generate_template
from .scaffolding.workflows import generate_workflow
from .scaffolding.hooks import setup_hook
from .scaffolding.github_templates import generate_github_templates
from .backup import create_backup, restore_backup

console = Console()
app = typer.Typer(
    name="git-auto",
    help="🚀 Complete Git + GitHub automation CLI tool",
    add_completion=False,
)

# ============================================================================
# AUTHENTICATION COMMANDS
# ============================================================================

@app.command()
def login(
    token: Optional[str] = typer.Option(None, "--token", "-t", help="GitHub Personal Access Token")
):
    """🔐 Login to GitHub using Personal Access Token."""
    login_github(token)

@app.command()
def logout(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """🚪 Logout and clear stored GitHub token."""
    from .github import clear_stored_token
    
    if not confirm:
        confirm = typer.confirm("Are you sure you want to logout?")
    
    if confirm:
        clear_stored_token()
        console.print("[bold green]✓ Logged out successfully[/bold green]")
    else:
        console.print("[yellow]Logout cancelled[/yellow]")

# ============================================================================
# REPOSITORY COMMANDS
# ============================================================================

@app.command()
def create_repo(
    name: str = typer.Argument(..., help="Repository name"),
    private: bool = typer.Option(False, "--private", "-p", help="Create private repository"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    homepage: Optional[str] = typer.Option(None, "--homepage", "-h"),
    topics: Optional[str] = typer.Option(None, "--topics", "-t", help="Comma-separated topics"),
    auto_init: bool = typer.Option(False, "--auto-init", help="Initialize with README"),
):
    """📦 Create a new GitHub repository."""
    topics_list = [t.strip() for t in topics.split(",")] if topics else None
    create_github_repo(name, private, description, homepage, topics_list, auto_init)


@app.command()
def init(
    connect: Optional[str] = typer.Option(None, "--connect", "-c", help="Connect to remote URL")
):
    """🎬 Initialize Git repository in current directory."""
    git_init(connect)


# ============================================================================
# PROJECT CREATION
# ============================================================================

@app.command()
def new(
    project_name: str = typer.Argument(..., help="Project name"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Project template"),
    private: bool = typer.Option(False, "--private", "-p", help="Create private repository"),
    no_github: bool = typer.Option(False, "--no-github", help="Skip GitHub repository creation"),
):
    """✨ Create a complete new project with Git + GitHub setup."""
    create_new_project(project_name, template, private, no_github)


# ============================================================================
# BASIC GIT COMMANDS
# ============================================================================

@app.command()
def add(
    files: Optional[List[str]] = typer.Argument(None, help="Files to add (default: all)"),
    all: bool = typer.Option(False, "--all", "-A", help="Add all files"),
):
    """➕ Stage files for commit."""
    git_add(files, all)


@app.command()
def commit(
    message: Optional[str] = typer.Argument(None, help="Commit message"),
    conventional: bool = typer.Option(False, "--conventional", "-c", help="Use conventional commit format"),
    amend: bool = typer.Option(False, "--amend", help="Amend previous commit"),
    safe: bool = typer.Option(False, "--safe", help="Use safe commit flow (test branch + PR)"),
):
    """💾 Commit staged changes."""
    config = load_config()
    use_safe = safe or config.get("safe_mode", False)
    
    if use_safe:
        if not message:
            console.print("[red]✗ Commit message required for safe mode[/red]")
            raise typer.Exit(1)
        from .commands.safe_flow import safe_push
        safe_push(message)
    else:
        if not message:
            console.print("[red]✗ Commit message required[/red]")
            raise typer.Exit(1)
        git_commit(message, conventional, amend)


@app.command()
def push(
    message: Optional[str] = typer.Argument(None, help="Commit message (auto add + commit + push)"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch to push (default: from config)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force push"),
    safe: bool = typer.Option(False, "--safe", help="Use safe commit flow (test branch + PR)"),
):
    """⬆️ Push commits to remote."""
    config = load_config()
    use_safe = safe or config.get("safe_mode", False)
    
    if use_safe and message:
        from .commands.safe_flow import safe_push
        safe_push(message)
    else:
        git_push(message, branch, force)


@app.command()
def pull(
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch to pull"),
    rebase: bool = typer.Option(False, "--rebase", "-r", help="Rebase instead of merge"),
    no_rebase: bool = typer.Option(False, "--no-rebase", help="Merge instead of rebase (default)"),
    ff_only: bool = typer.Option(False, "--ff-only", help="Only allow fast-forward"),
):
    """⬇️ Pull changes from remote."""
    git_pull(branch, rebase, no_rebase, ff_only)


@app.command()
def status(
    short: bool = typer.Option(False, "--short", "-s", help="Short format"),
):
    """📊 Show working tree status."""
    git_status(short)


@app.command()
def log(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of commits to show"),
    oneline: bool = typer.Option(False, "--oneline", help="One line per commit"),
    graph: bool = typer.Option(False, "--graph", "-g", help="Show commit graph"),
):
    """📜 Show commit history."""
    git_log(limit, oneline, graph)


# ============================================================================
# BRANCH COMMANDS
# ============================================================================

@app.command()
def branch(
    name: Optional[str] = typer.Argument(None, help="Branch name to create"),
    list: bool = typer.Option(False, "--list", "-l", help="List all branches"),
    remote: bool = typer.Option(False, "--remote", "-r", help="List remote branches"),
):
    """🌿 Create or list branches."""
    git_branch(name, list, remote)


@app.command()
def switch(
    name: str = typer.Argument(..., help="Branch name to switch to"),
    create: bool = typer.Option(False, "--create", "-c", help="Create branch if it doesn't exist"),
):
    """🔄 Switch to a different branch."""
    git_switch(name, create)


@app.command()
def delete_branch(
    name: str = typer.Argument(..., help="Branch name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Force delete"),
):
    """🗑️ Delete a branch."""
    git_delete_branch(name, force)


# ============================================================================
# STASH COMMANDS
# ============================================================================

@app.command()
def stash(
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Stash message"),
    list: bool = typer.Option(False, "--list", "-l", help="List all stashes"),
):
    """💼 Stash uncommitted changes."""
    git_stash(message, list)


@app.command()
def stash_apply(
    index: int = typer.Option(0, "--index", "-i", help="Stash index to apply"),
    pop: bool = typer.Option(False, "--pop", "-p", help="Apply and remove stash"),
):
    """📤 Apply stashed changes."""
    git_stash_apply(index, pop)


# ============================================================================
# MERGE COMMANDS
# ============================================================================

@app.command()
def merge(
    branch: str = typer.Argument(..., help="Branch to merge"),
    no_ff: bool = typer.Option(False, "--no-ff", help="No fast-forward merge"),
    squash: bool = typer.Option(False, "--squash", help="Squash commits"),
):
    """🔗 Merge branches."""
    git_merge(branch, no_ff, squash)


# ============================================================================
# CLONE COMMAND
# ============================================================================

@app.command()
def clone(
    url: str = typer.Argument(..., help="Repository URL to clone"),
    directory: Optional[str] = typer.Option(None, "--dir", "-d", help="Target directory"),
    depth: Optional[int] = typer.Option(None, "--depth", help="Shallow clone depth"),
):
    """📥 Clone a repository."""
    git_clone(url, directory, depth)


# ============================================================================
# STATISTICS
# ============================================================================

@app.command()
def stats(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed statistics"),
):
    """📈 Show repository statistics."""
    git_stats(detailed)


# ============================================================================
# GENERATORS
# ============================================================================

@app.command()
def readme(
    interactive: bool = typer.Option(True, "--interactive", "-i", help="Interactive mode"),
    output: str = typer.Option("README.md", "--output", "-o", help="Output file"),
):
    """📝 Generate professional README.md."""
    generate_readme(interactive, output)


@app.command()
def license(
    type: Optional[str] = typer.Option(None, "--type", "-t", help="License type"),
    author: Optional[str] = typer.Option(None, "--author", "-a", help="Author name"),
    year: Optional[int] = typer.Option(None, "--year", "-y", help="Copyright year"),
):
    """⚖️ Generate LICENSE file."""
    generate_license(type, author, year)


@app.command()
def ignore(
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Template type"),
):
    """🚫 Generate .gitignore file."""
    generate_gitignore(template)


@app.command()
def template(
    type: str = typer.Argument(..., help="Template type (python, node, cpp, web, etc.)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """📋 Generate project template structure."""
    generate_template(type, output)


# ============================================================================
# WORKFLOWS & HOOKS
# ============================================================================

@app.command()
def workflow(
    type: str = typer.Argument(..., help="Workflow type (ci, cd, test, etc.)"),
    platform: str = typer.Option("github", "--platform", "-p", help="CI platform"),
):
    """⚙️ Generate CI/CD workflow files."""
    generate_workflow(type, platform)


@app.command()
def hook(
    type: str = typer.Argument(..., help="Hook type (pre-commit, pre-push, etc.)"),
    script: Optional[str] = typer.Option(None, "--script", "-s", help="Custom script path"),
):
    """🪝 Setup Git hooks."""
    setup_hook(type, script)


# ============================================================================
# GITHUB TEMPLATES
# ============================================================================

@app.command()
def templates(
    type: str = typer.Argument(..., help="Template type (issue, pr, contributing)"),
):
    """📋 Generate GitHub issue/PR templates."""
    generate_github_templates(type)


# ============================================================================
# COLLABORATION
# ============================================================================

@app.command()
def collab(
    username: str = typer.Argument(..., help="GitHub username to add"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    permission: str = typer.Option("push", "--permission", "-p", help="Permission level"),
):
    """👥 Add collaborator to repository."""
    add_collaborator(username, repo, permission)


@app.command()
def protect(
    branch: str = typer.Argument("main", help="Branch to protect"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
):
    """🛡️ Setup branch protection rules."""
    protect_branch(branch, repo)


# ============================================================================
# GITHUB ISSUES
# ============================================================================

issue_app = typer.Typer(help="🐛 GitHub Issues Management")
app.add_typer(issue_app, name="issue")


@issue_app.command("create")
def issue_create(
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Issue title"),
    body: Optional[str] = typer.Option(None, "--body", "-b", help="Issue description"),
    labels: Optional[str] = typer.Option(None, "--labels", "-l", help="Comma-separated labels"),
    assignees: Optional[str] = typer.Option(None, "--assignees", "-a", help="Comma-separated assignees"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
):
    
    if not title:
        title = questionary.text("Issue title:").ask()
        if not title:
            console.print("[red]✗ Title is required[/red]")
            return
    
    if not body:
        body = questionary.text("Issue description (optional):").ask()
    
    labels_list = [l.strip() for l in labels.split(",")] if labels else None
    assignees_list = [a.strip() for a in assignees.split(",")] if assignees else None
    
    create_issue(title, body, labels_list, assignees_list, repo)


@issue_app.command("list")
def issue_list(
    state: str = typer.Option("open", "--state", "-s", help="Issue state (open/closed/all)"),
    labels: Optional[str] = typer.Option(None, "--labels", "-l", help="Filter by labels"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Filter by assignee"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    limit: int = typer.Option(30, "--limit", "-n", help="Number of issues to show"),
):
    """List GitHub issues."""
    
    list_issues(state, labels, assignee, repo, limit)


@issue_app.command("view")
def issue_view(
    number: int = typer.Argument(..., help="Issue number"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
):
    """View details of a specific issue."""
    
    get_issue(number, repo)


@issue_app.command("close")
def issue_close(
    number: int = typer.Argument(..., help="Issue number"),
    comment: Optional[str] = typer.Option(None, "--comment", "-c", help="Closing comment"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
):
    """Close a GitHub issue."""
    
    close_issue(number, comment, repo)


@issue_app.command("update")
def issue_update(
    number: int = typer.Argument(..., help="Issue number"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    body: Optional[str] = typer.Option(None, "--body", "-b", help="New description"),
    state: Optional[str] = typer.Option(None, "--state", "-s", help="New state (open/closed)"),
    labels: Optional[str] = typer.Option(None, "--labels", "-l", help="Comma-separated labels"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
):
    """Update a GitHub issue."""
    
    labels_list = [l.strip() for l in labels.split(",")] if labels else None
    
    update_issue(number, title, body, state, labels_list, repo)


# ============================================================================
# BACKUP & RESTORE
# ============================================================================

@app.command()
def backup(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Backup location"),
):
    """💾 Create repository backup."""
    create_backup(output)


@app.command()
def restore(
    backup_path: str = typer.Argument(..., help="Backup file path"),
):
    """♻️ Restore from backup."""
    restore_backup(backup_path)


# ============================================================================
# CONFIGURATION
# ============================================================================

config_app = typer.Typer(help="⚙️ Configuration management")
app.add_typer(config_app, name="config")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value"),
):
    """Set configuration value."""
    set_config(key, value)


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Configuration key"),
):
    """Get configuration value."""
    value = get_config(key)
    if value:
        console.print(f"[bold cyan]{key}:[/bold cyan] {value}")
    else:
        console.print(f"[yellow]No value set for '{key}'[/yellow]")


@config_app.command("list")
def config_list():
    """List all configuration values."""
    list_config()


@config_app.command("reset")
def config_reset(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Reset configuration to defaults."""
    if not confirm:
        confirm = typer.confirm("Are you sure you want to reset all configuration?")
    if confirm:
        reset_config()


# ============================================================================
# VERSION & HELP
# ============================================================================

@app.command()
def version():
    """📌 Show version information."""
    from . import __version__
    
    version_text = (
        f"[bold cyan]Git-Auto Pro[/bold cyan]\n"
        f"Version: [yellow]{__version__}[/yellow]\n"
        f"Complete Git + GitHub Automation Tool"
    )
    
    console.print(Panel(
        version_text,
        border_style="cyan"
    ))

# ============================================================================
# GITIGNORE MANAGER
# ============================================================================

@app.command()
def ignore_manager():
    """🎯 Interactive .gitignore file manager - browse and select files."""
    from .gitignore_manager import interactive_gitignore_manager
    
    interactive_gitignore_manager()


# ============================================================================
# UNDO COMMAND
# ============================================================================

@app.command()
def undo(
    hard: bool = typer.Option(False, "--hard", help="Hard reset: discard all changes"),
    push_flag: bool = typer.Option(False, "--push", help="Soft undo + force push"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """⏪ Undo last commit."""
    git_undo(hard=hard, force_push=push_flag, confirm=yes)


# ============================================================================
# RELEASE COMMAND
# ============================================================================

@app.command()
def release(
    version: str = typer.Argument(..., help="Version (1.2.0) or bump type (patch/minor/major)"),
    draft: bool = typer.Option(False, "--draft", help="Create draft release"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Release notes"),
):
    """🚀 Create a release — tag, push, and GitHub release."""
    from .commands.release import create_release
    create_release(version, draft, notes)


# ============================================================================
# DOCTOR COMMAND
# ============================================================================

@app.command()
def doctor():
    """🩺 Run system diagnostics."""
    from .commands.doctor import run_diagnostics
    run_diagnostics()


# ============================================================================
# PR COMMANDS
# ============================================================================

@app.command()
def pr(
    title: str = typer.Argument(..., help="PR title"),
    draft: bool = typer.Option(False, "--draft", help="Create draft PR"),
    reviewer: Optional[List[str]] = typer.Option(None, "--reviewer", "-r", help="Request reviewer"),
    label: Optional[List[str]] = typer.Option(None, "--label", "-l", help="Add label"),
    base: Optional[str] = typer.Option(None, "--base", "-b", help="Base branch (default: from config)"),
):
    """📋 Create a Pull Request from current branch."""
    from .github_pr.pr_manager import create_pull_request
    from .config import get_default_branch
    import git
    
    try:
        repo = git.Repo(".", search_parent_directories=True)
        head = str(repo.active_branch)
        base_branch = base or load_config().get("pr_base_branch", get_default_branch())
        
        if head == base_branch:
            console.print(f"[red]✗ You're on '{head}' — switch to a feature branch first.[/red]")
            raise typer.Exit(1)
        
        create_pull_request(
            head=head,
            base=base_branch,
            title=title,
            draft=draft,
            reviewers=reviewer,
            labels=label,
        )
    except git.InvalidGitRepositoryError:
        console.print("[red]✗ Not a git repository.[/red]")


@app.command()
def prs(
    state: str = typer.Option("open", "--state", "-s", help="PR state (open/closed/all)"),
):
    """📋 List pull requests for current repo."""
    from .github_pr.pr_manager import list_pull_requests
    list_pull_requests(state)


@app.command(name="merge-pr")
def merge_pr(
    number: int = typer.Argument(..., help="PR number to merge"),
    squash: bool = typer.Option(False, "--squash", help="Squash merge"),
    rebase: bool = typer.Option(False, "--rebase", help="Rebase merge"),
):
    """🔗 Merge a pull request by number."""
    from .github_pr.pr_manager import merge_pull_request
    
    if squash:
        method = "squash"
    elif rebase:
        method = "rebase"
    else:
        method = "merge"
    
    merge_pull_request(number, method)


@app.command(name="review-pr")
def review_pr(
    number: int = typer.Argument(..., help="PR number to review"),
):
    """👀 Open a PR in the browser for review."""
    from .github_pr.pr_manager import review_pr_in_browser
    review_pr_in_browser(number)


if __name__ == "__main__":
    app()