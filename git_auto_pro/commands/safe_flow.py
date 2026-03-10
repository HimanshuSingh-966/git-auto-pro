"""Safe commit flow — test branch + PR creation."""

import git
import time
from typing import Optional
from rich.console import Console
from rich.panel import Panel

from ..config import load_config, get_default_branch
from ..github_pr.pr_manager import create_pull_request

console = Console()


def safe_push(
    message: str,
    feature_name: Optional[str] = None,
) -> None:
    """Execute safe commit flow: create test branch, commit, push, create PR."""
    try:
        repo = git.Repo(".", search_parent_directories=True)
        git_cmd = getattr(repo, 'git')
        config = load_config()
        
        prefix = config.get("test_branch_prefix", "test")
        base_branch = config.get("pr_base_branch", get_default_branch())
        
        # Detect current branch
        try:
            current_branch = str(repo.active_branch)
        except TypeError:
            current_branch = get_default_branch()
        
        # Determine test branch name
        if feature_name:
            test_branch = f"{prefix}/{feature_name}"
        else:
            test_branch = f"{prefix}/{current_branch}"
        
        # Handle branch name collisions
        existing_branches = [str(b) for b in repo.branches]
        if test_branch in existing_branches:
            # Check if remote also has it
            try:
                remote_refs = [str(ref).replace("origin/", "") for ref in repo.remotes.origin.refs]
                if test_branch in remote_refs:
                    # Collision — append timestamp
                    timestamp = int(time.time())
                    test_branch = f"{test_branch}-{timestamp}"
                    console.print(f"[yellow]⚠ Branch collision detected, using: {test_branch}[/yellow]")
            except Exception:
                pass
        
        # Stage all changes
        git_cmd.add(A=True)
        
        # Check if there's anything to commit
        if not repo.index.diff("HEAD") and not repo.index.diff(None):
            # Additional check for new files
            try:
                staged = git_cmd.diff("--cached", "--name-only")
                if not staged.strip():
                    console.print("[yellow]⚠ Nothing staged. Use 'git-auto add' first.[/yellow]")
                    return
            except Exception:
                if not repo.index.entries:
                    console.print("[yellow]⚠ Nothing staged. Use 'git-auto add' first.[/yellow]")
                    return
        
        # Create and switch to test branch
        if test_branch in existing_branches:
            git_cmd.checkout(test_branch)
        else:
            git_cmd.checkout("-b", test_branch)
        console.print(f"[green]✓ Switched to: {test_branch}[/green]")
        
        # Commit changes
        repo.index.commit(message)
        console.print(f"[green]✓ Committed: {message}[/green]")
        
        # Push to remote
        if repo.remotes:
            git_cmd.push("origin", test_branch, "--set-upstream")
            console.print(f"[green]✓ Pushed to: {test_branch}[/green]")
        else:
            console.print("[yellow]⚠ No remote configured — skipped push[/yellow]")
            return
        
        # Auto-create PR if configured
        auto_pr = config.get("auto_create_pr", True)
        if auto_pr:
            try:
                # Generate PR body with diff summary
                try:
                    diff_stat = git_cmd.diff("--stat", f"origin/{base_branch}..{test_branch}")
                except Exception:
                    diff_stat = "Could not generate diff summary"
                
                pr_body = f"""## Changes

{message}

### Diff Summary
```
{diff_stat}
```

### Review Checklist
- [ ] Code reviewed
- [ ] Tests pass
- [ ] Documentation updated
"""
                
                pr_data = create_pull_request(
                    head=test_branch,
                    base=base_branch,
                    title=message,
                    body=pr_body,
                )
                
                # Display summary panel
                panel_content = (
                    f"  [green]✓[/green] Committed to:  [cyan]{test_branch}[/cyan]\n"
                    f"  [green]✓[/green] PR Created:    [cyan]#{pr_data['number']}[/cyan]\n"
                    f"  → Review at:     [link={pr_data['html_url']}]{pr_data['html_url']}[/link]\n"
                    f"\n"
                    f"  When ready:  [bold]git-auto merge-pr {pr_data['number']}[/bold]"
                )
                console.print(Panel(panel_content, title="Safe Push Complete", border_style="green"))
                
            except Exception as e:
                console.print(f"[yellow]⚠ Push completed but PR creation failed: {e}[/yellow]")
                console.print(f"[cyan]→ Create PR manually at: https://github.com[/cyan]")
        else:
            console.print(Panel(
                f"  [green]✓[/green] Committed to: [cyan]{test_branch}[/cyan]\n"
                f"  → Create a PR when ready: [bold]git-auto pr \"{message}\"[/bold]",
                title="Safe Push Complete",
                border_style="green"
            ))
        
    except git.InvalidGitRepositoryError:
        console.print("[red]✗ Not a git repository. Run 'git-auto init' first.[/red]")
    except Exception as e:
        console.print(f"[red]✗ Safe push failed: {e}[/red]")
