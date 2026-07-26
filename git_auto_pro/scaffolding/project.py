"""Complete project creation module."""

from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary

console = Console()


def create_new_project(
    project_name: str,
    template: Optional[str] = None,
    private: bool = False,
    no_github: bool = False,
) -> None:
    """Create a complete new project."""
    from ..git_commands import git_init, git_add, git_commit, git_push
    from ..github import create_github_repo, get_current_user
    from ..config import get_default_branch
    from .readme import generate_readme
    from .license import generate_license
    from .gitignore import generate_gitignore
    from .templates import generate_template

    console.print(f"[bold cyan]✨ Creating project: {project_name}[/bold cyan]\n")
    
    # Create project directory
    project_path = Path(project_name)
    if project_path.exists():
        console.print(f"[red]✗ Directory '{project_name}' already exists[/red]")
        return
    
    project_path.mkdir()
    import os
    os.chdir(project_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Generate project structure
        task = progress.add_task("Generating project files...", total=None)
        
        if template:
            generate_template(template, ".")
        
        generate_gitignore(template)
        generate_readme(interactive=False, output="README.md")
        generate_license(type=None, author=None, year=None)
        
        progress.update(task, description="Initializing Git repository...")
        git_init()
        
        progress.update(task, description="Creating initial commit...")
        git_add(all=True)
        git_commit("Initial commit")
        
        if not no_github:
            progress.update(task, description="Creating GitHub repository...")
            try:
                user = get_current_user()
                repo_data = create_github_repo(
                    project_name,
                    private=private,
                    description=f"Project: {project_name}",
                )

                # Connect to remote
                import git
                repo = git.Repo(".")

                # Align the local branch with the configured default branch
                # before pushing, so the push target actually exists locally
                # (git's own initial branch may be master/main depending on
                # version/config).
                default_branch = get_default_branch()
                try:
                    repo.git.branch("-M", default_branch)
                except Exception:
                    pass

                repo.create_remote("origin", repo_data["clone_url"])

                progress.update(task, description="Pushing to GitHub...")
                git_push(branch=default_branch)

            except Exception as e:
                console.print(f"[yellow]⚠ Could not create GitHub repo: {e}[/yellow]")
    
    console.print(f"\n[bold green]✓ Project created successfully![/bold green]")
    console.print(f"[cyan]Location:[/cyan] {project_path.absolute()}")

