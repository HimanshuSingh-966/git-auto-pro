"""Release management — tag, push, GitHub release."""

import re
import git
import tomllib
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel

console = Console()

VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
PYPROJECT_PATH = "pyproject.toml"


def _read_current_version() -> str:
    """Read current version from pyproject.toml (canonical source)."""
    pyproject = Path(PYPROJECT_PATH)
    if not pyproject.exists():
        # Fallback: check for __init__.py
        init_file = Path("git_auto_pro/__init__.py")
        if init_file.exists():
            content = init_file.read_text()
            match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
        raise FileNotFoundError("Cannot find version in pyproject.toml or __init__.py")
    
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    
    return data.get("project", {}).get("version", "0.0.0")


def _bump_version(current: str, bump_type: str) -> str:
    """Bump version based on type (patch/minor/major)."""
    match = VERSION_PATTERN.match(current)
    if not match:
        raise ValueError(f"Invalid version format: {current}")
    
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def _update_version_files(new_version: str) -> None:
    """Update version in pyproject.toml, setup.py, and __init__.py."""
    # Update pyproject.toml
    pyproject = Path(PYPROJECT_PATH)
    if pyproject.exists():
        content = pyproject.read_text()
        content = re.sub(
            r'version\s*=\s*"[^"]+"',
            f'version = "{new_version}"',
            content,
            count=1
        )
        pyproject.write_text(content)
        console.print(f"[green]✓ Updated pyproject.toml → {new_version}[/green]")
    
    # Sync __init__.py
    init_file = Path("git_auto_pro/__init__.py")
    if init_file.exists():
        content = init_file.read_text()
        content = re.sub(
            r'__version__\s*=\s*"[^"]+"',
            f'__version__ = "{new_version}"',
            content
        )
        init_file.write_text(content)
        console.print(f"[green]✓ Synced __init__.py → {new_version}[/green]")
    
    # Sync setup.py
    setup_file = Path("setup.py")
    if setup_file.exists():
        content = setup_file.read_text()
        content = re.sub(
            r'version\s*=\s*"[^"]+"',
            f'version="{new_version}"',
            content,
            count=1
        )
        setup_file.write_text(content)
        console.print(f"[green]✓ Synced setup.py → {new_version}[/green]")


def _generate_changelog(repo: git.Repo, since_tag: Optional[str] = None) -> str:
    """Generate changelog from conventional commits since last tag."""
    categories = {
        "feat": [],
        "fix": [],
        "docs": [],
        "refactor": [],
        "test": [],
        "chore": [],
        "other": [],
    }
    
    try:
        if since_tag:
            commits = list(repo.iter_commits(f"{since_tag}..HEAD"))
        else:
            commits = list(repo.iter_commits(max_count=50))
    except Exception:
        return "No commits found for changelog generation."
    
    for commit in commits:
        msg = str(commit.message).strip().split("\n")[0]
        categorized = False
        for prefix in categories:
            if prefix == "other":
                continue
            if msg.lower().startswith(f"{prefix}:") or msg.lower().startswith(f"{prefix}("):
                categories[prefix].append(msg)
                categorized = True
                break
        if not categorized:
            categories["other"].append(msg)
    
    changelog_parts = []
    labels = {
        "feat": "✨ Features",
        "fix": "🐛 Bug Fixes",
        "docs": "📚 Documentation",
        "refactor": "♻️ Refactoring",
        "test": "🧪 Tests",
        "chore": "🔧 Chores",
        "other": "📝 Other Changes",
    }
    
    for key, label in labels.items():
        if categories[key]:
            changelog_parts.append(f"### {label}")
            for msg in categories[key]:
                changelog_parts.append(f"- {msg}")
            changelog_parts.append("")
    
    return "\n".join(changelog_parts) if changelog_parts else "No notable changes."


def create_release(
    version_or_bump: str,
    draft: bool = False,
    notes: Optional[str] = None,
) -> None:
    """Create a release: tag, push, and optionally create GitHub release."""
    try:
        repo = git.Repo(".", search_parent_directories=True)
        git_cmd = getattr(repo, 'git')
        
        # Determine new version
        current_version = _read_current_version()
        
        if version_or_bump in ("patch", "minor", "major"):
            new_version = _bump_version(current_version, version_or_bump)
            console.print(f"[cyan]Bumping: {current_version} → {new_version} ({version_or_bump})[/cyan]")
        elif VERSION_PATTERN.match(version_or_bump):
            new_version = version_or_bump
            console.print(f"[cyan]Setting version: {new_version}[/cyan]")
        else:
            console.print(f"[red]✗ Invalid version: {version_or_bump}. Use 'patch', 'minor', 'major', or 'X.Y.Z'[/red]")
            return
        
        # Update version files
        _update_version_files(new_version)
        
        # Generate changelog
        last_tag = None
        try:
            tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime, reverse=True)
            if tags:
                last_tag = str(tags[0])
        except Exception:
            pass
        
        changelog = _generate_changelog(repo, last_tag)
        
        if notes:
            release_notes = notes
        else:
            release_notes = f"## v{new_version}\n\n{changelog}"
        
        # Commit version bump
        git_cmd.add(A=True)
        repo.index.commit(f"chore: release v{new_version}")
        console.print(f"[green]✓ Version bump committed[/green]")
        
        # Create tag
        tag_name = f"v{new_version}"
        repo.create_tag(tag_name, message=f"Release {tag_name}")
        console.print(f"[green]✓ Tag created: {tag_name}[/green]")
        
        # Push commit + tag
        if repo.remotes:
            try:
                branch = str(repo.active_branch)
                git_cmd.push("origin", branch)
                git_cmd.push("origin", tag_name)
                console.print(f"[green]✓ Pushed to remote[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠ Push failed: {e}[/yellow]")
        
        # Create GitHub release
        if repo.remotes:
            try:
                from ..github import get_authenticated_session, get_current_user, GITHUB_API_URL
                
                session = get_authenticated_session()
                user = get_current_user()
                
                remote_url = repo.remotes.origin.url
                repo_name = remote_url.split("/")[-1].replace(".git", "")
                
                release_data = {
                    "tag_name": tag_name,
                    "name": f"v{new_version}",
                    "body": release_notes,
                    "draft": draft,
                    "prerelease": False,
                }
                
                response = session.post(
                    f"{GITHUB_API_URL}/repos/{user['login']}/{repo_name}/releases",
                    json=release_data,
                    timeout=10
                )
                response.raise_for_status()
                release = response.json()
                
                status = "Draft release" if draft else "Release"
                console.print(f"[green]✓ {status} created: {release['html_url']}[/green]")
                
            except Exception as e:
                console.print(f"[yellow]⚠ GitHub release creation failed: {e}[/yellow]")
                console.print("[yellow]→ Tag was still pushed. Create release manually on GitHub.[/yellow]")
        
        # Summary
        console.print(Panel(
            f"  Version: [bold cyan]v{new_version}[/bold cyan]\n"
            f"  Tag:     [bold]{tag_name}[/bold]\n"
            f"  Status:  [green]{'Draft' if draft else 'Published'}[/green]",
            title="Release Complete",
            border_style="green"
        ))
        
    except git.InvalidGitRepositoryError:
        console.print("[red]✗ Not a git repository. Run 'git-auto init' first.[/red]")
    except FileNotFoundError as e:
        console.print(f"[red]✗ {e}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Release failed: {e}[/red]")
