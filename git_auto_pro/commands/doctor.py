"""git-auto doctor — System diagnostics."""

import sys
import shutil
import subprocess
import git
import requests
from typing import Optional
from rich.console import Console
from rich.table import Table

from ..config import load_config, get_default_branch

console = Console()


def run_diagnostics() -> None:
    """Run full system diagnostics and print results."""
    console.print("\n[bold cyan]🔍 git-auto-pro diagnostics[/bold cyan]\n")
    
    results = Table(show_header=False, box=None, padding=(0, 2))
    results.add_column("Status", width=4)
    results.add_column("Check", style="white", width=25)
    results.add_column("Value", style="cyan")
    results.add_column("Fix", style="yellow")
    
    # 1. Git installed
    git_path = shutil.which("git")
    if git_path:
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
            git_version = result.stdout.strip()
            results.add_row("[green]✓[/green]", "Git installed", git_version, "")
        except Exception:
            results.add_row("[green]✓[/green]", "Git installed", "found", "")
    else:
        results.add_row("[red]✗[/red]", "Git installed", "not found", "Install Git from git-scm.com")
    
    # 2. Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 8):
        results.add_row("[green]✓[/green]", "Python version", py_version, "")
    else:
        results.add_row("[red]✗[/red]", "Python version", py_version, "Python 3.8+ required")
    
    # 3. GitHub token
    from ..github import get_stored_token, check_api_connectivity
    token = get_stored_token()
    if token:
        if check_api_connectivity():
            # Validate token
            from ..github import validate_token
            # We do a quiet check — don't print extra output
            try:
                headers = {
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                response = requests.get("https://api.github.com/user", headers=headers, timeout=5)
                if response.status_code == 200:
                    username = response.json().get("login", "unknown")
                    results.add_row("[green]✓[/green]", "GitHub token", f"valid (user: {username})", "")
                else:
                    results.add_row("[red]✗[/red]", "GitHub token", "invalid", "Run: git-auto login")
            except Exception:
                results.add_row("[yellow]⚠[/yellow]", "GitHub token", "stored but couldn't validate", "Check internet connection")
        else:
            results.add_row("[yellow]⚠[/yellow]", "GitHub token", "stored (offline)", "GitHub API unreachable")
    else:
        results.add_row("[red]✗[/red]", "GitHub token", "not configured", "Run: git-auto login")
    
    # 4. Remote configured
    try:
        repo = git.Repo(".", search_parent_directories=True)
        
        if repo.remotes:
            origin = repo.remotes.origin
            results.add_row("[green]✓[/green]", "Remote configured", f"origin → {origin.url}", "")
        else:
            results.add_row("[red]✗[/red]", "Remote configured", "none", "Run: git-auto init --connect <url>")
        
        # 5. Branch consistency
        config = load_config()
        config_branch = config.get("default_branch", "main")
        try:
            current = str(repo.active_branch)
            if current == config_branch:
                results.add_row("[green]✓[/green]", "Branch match", f"local={current}, config={config_branch}", "")
            else:
                results.add_row(
                    "[yellow]⚠[/yellow]", "Branch mismatch",
                    f"local={current}, config={config_branch}",
                    f"Fix: git-auto config set default_branch {current}"
                )
        except TypeError:
            results.add_row("[yellow]⚠[/yellow]", "Branch", "detached HEAD", "Switch to a branch")
        
        # 6. Untracked files
        untracked = repo.untracked_files
        if untracked:
            results.add_row(
                "[yellow]⚠[/yellow]", "Untracked files",
                f"{len(untracked)} files not staged",
                "Fix: git-auto add --all"
            )
        else:
            results.add_row("[green]✓[/green]", "Untracked files", "none", "")
        
        # 7. Uncommitted changes
        changed = [item.a_path for item in repo.index.diff(None)]
        if changed:
            results.add_row(
                "[yellow]⚠[/yellow]", "Uncommitted changes",
                f"{len(changed)} modified files",
                "Fix: git-auto commit \"message\""
            )
        else:
            results.add_row("[green]✓[/green]", "Uncommitted changes", "none", "")
            
    except git.InvalidGitRepositoryError:
        results.add_row("[red]✗[/red]", "Git repository", "not found", "Run: git-auto init")
    
    # 8. Safe mode check
    config = load_config()
    safe_mode = config.get("safe_mode", False)
    if safe_mode:
        results.add_row("[green]✓[/green]", "Safe mode", "enabled", "")
    else:
        results.add_row(
            "[yellow]⚠[/yellow]", "Safe mode", "disabled",
            "Enable: git-auto config set safe_mode true"
        )
    
    console.print(results)
    console.print()
