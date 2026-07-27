"""git-auto doctor — System diagnostics."""

import sys
import shutil
import subprocess
import git
import requests
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table

from ..config import load_config

console = Console()

# Status -> (icon, color) for the rendered table.
_STATUS_STYLE = {
    "ok": ("✓", "green"),
    "warn": ("⚠", "yellow"),
    "fail": ("✗", "red"),
}


def _row(results: List[Dict[str, Any]], status: str, check: str, value: Any, fix: str = "") -> None:
    results.append({"status": status, "check": check, "value": value, "fix": fix})


def run_diagnostics(json_output: bool = False) -> List[Dict[str, Any]]:
    """Run full system diagnostics. Returns a list of result dicts and, unless
    json_output is set, prints a rendered table."""
    if not json_output:
        console.print("\n[bold cyan]🔍 git-auto-pro diagnostics[/bold cyan]\n")

    results: List[Dict[str, Any]] = []

    # 1. Git installed
    git_path = shutil.which("git")
    if git_path:
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
            git_version = result.stdout.strip()
            _row(results, "ok", "Git installed", git_version)
        except Exception:
            _row(results, "ok", "Git installed", "found")
    else:
        _row(results, "fail", "Git installed", "not found", "Install Git from git-scm.com")

    # 2. Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 8):
        _row(results, "ok", "Python version", py_version)
    else:
        _row(results, "fail", "Python version", py_version, "Python 3.8+ required")

    # 3. GitHub token + scopes
    from ..github import get_stored_token, check_api_connectivity, _auth_headers, GITHUB_API_URL
    token = get_stored_token()
    if token:
        if check_api_connectivity():
            try:
                response = requests.get(
                    f"{GITHUB_API_URL}/user",
                    headers=_auth_headers(token),
                    timeout=5,
                )
                if response.status_code == 200:
                    username = response.json().get("login", "unknown")
                    # Inspect token scopes from the response header.
                    scopes_header = response.headers.get("X-OAuth-Scopes")
                    if isinstance(scopes_header, str) and scopes_header.strip():
                        scopes = [s.strip() for s in scopes_header.split(",") if s.strip()]
                        missing = [s for s in ("repo", "workflow") if s not in scopes]
                        if missing:
                            _row(
                                results, "warn", "GitHub token",
                                f"valid (user: {username}); scopes: {', '.join(scopes) or 'none'}",
                                f"Token missing scope(s): {', '.join(missing)}. Regenerate at https://github.com/settings/tokens",
                            )
                        else:
                            _row(results, "ok", "GitHub token", f"valid (user: {username}); scopes: {', '.join(scopes)}")
                    else:
                        _row(results, "ok", "GitHub token", f"valid (user: {username})")
                else:
                    _row(results, "fail", "GitHub token", "invalid", "Run: git-auto login")
            except Exception:
                _row(results, "warn", "GitHub token", "stored but couldn't validate", "Check internet connection")
        else:
            _row(results, "warn", "GitHub token", "stored (offline)", "GitHub API unreachable")
    else:
        _row(results, "fail", "GitHub token", "not configured", "Run: git-auto login")

    # 4-7. Git-repo checks (skipped gracefully if not a repo).
    try:
        repo = git.Repo(".", search_parent_directories=True)

        # 4. Remote configured
        if repo.remotes:
            try:
                origin = repo.remotes.origin
                _row(results, "ok", "Remote configured", f"origin → {origin.url}")
            except Exception:
                _row(results, "warn", "Remote configured", "remotes exist but no 'origin'", "git-auto init --connect <url>")
        else:
            _row(results, "fail", "Remote configured", "none", "Run: git-auto init --connect <url>")

        # 5. Branch consistency
        config = load_config()
        config_branch = config.get("default_branch", "main")
        try:
            current = str(repo.active_branch)
            if current == config_branch:
                _row(results, "ok", "Branch match", f"local={current}, config={config_branch}")
            else:
                _row(
                    results, "warn", "Branch mismatch",
                    f"local={current}, config={config_branch}",
                    f"Fix: git-auto config set default_branch {current}",
                )
        except TypeError:
            _row(results, "warn", "Branch", "detached HEAD", "Switch to a branch")

        # 6. Upstream tracking + ahead/behind
        try:
            active = repo.active_branch
            upstream = active.tracking_branch()
            if upstream is None:
                _row(results, "warn", "Upstream tracking", "none", f"git branch --set-upstream-to=origin/{current}")
            else:
                upstream_name = str(upstream)
                ahead = len(list(repo.iter_commits(f"{upstream_name}..HEAD")))
                behind = len(list(repo.iter_commits(f"HEAD..{upstream_name}")))
                if ahead == 0 and behind == 0:
                    _row(results, "ok", "Upstream sync", f"up to date with {upstream_name}")
                else:
                    _row(
                        results, "warn", "Upstream sync",
                        f"{ahead} ahead, {behind} behind {upstream_name}",
                        "Fix: git-auto pull --rebase  (or  git-auto push)",
                    )
        except Exception:
            # Introspection not possible (detached HEAD, missing refs, mocks) — skip.
            pass

        # 7. Untracked files
        untracked = repo.untracked_files
        if untracked:
            _row(results, "warn", "Untracked files", f"{len(untracked)} files not staged", "Fix: git-auto add --all")
        else:
            _row(results, "ok", "Untracked files", "none")

        # 8. Uncommitted changes
        changed = [item.a_path for item in repo.index.diff(None)]
        if changed:
            _row(results, "warn", "Uncommitted changes", f"{len(changed)} modified files", 'Fix: git-auto commit "message"')
        else:
            _row(results, "ok", "Uncommitted changes", "none")

    except git.InvalidGitRepositoryError:
        _row(results, "fail", "Git repository", "not found", "Run: git-auto init")
    except Exception:
        # Non-repo environments / mocked git — don't crash diagnostics.
        _row(results, "fail", "Git repository", "not found", "Run: git-auto init")

    # 9. Safe mode
    config = load_config()
    safe_mode = config.get("safe_mode", False)
    if safe_mode:
        _row(results, "ok", "Safe mode", "enabled")
    else:
        _row(results, "warn", "Safe mode", "disabled", "Enable: git-auto config set safe_mode true")

    if not json_output:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Status", width=4)
        table.add_column("Check", style="white", width=25)
        table.add_column("Value", style="cyan")
        table.add_column("Fix", style="yellow")
        for r in results:
            icon, color = _STATUS_STYLE.get(r["status"], ("•", "white"))
            table.add_row(f"[{color}]{icon}[/{color}]", r["check"], str(r["value"]), r["fix"])
        console.print(table)
        console.print()

    return results
