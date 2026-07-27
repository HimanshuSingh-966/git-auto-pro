"""Git hooks setup module."""

from pathlib import Path
from typing import Optional
from rich.console import Console
import stat

console = Console()


def setup_hook(type: str, script: Optional[str] = None) -> None:
    """Setup Git hooks."""
    console.print(f"[bold cyan]🪝 Setting up {type} hook[/bold cyan]\n")
    
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        console.print("[red]✗ Not a git repository[/red]")
        return
    
    hook_scripts = {
        "pre-commit": PRE_COMMIT_HOOK,
        "pre-push": PRE_PUSH_HOOK,
        "commit-msg": COMMIT_MSG_HOOK,
        "post-commit": POST_COMMIT_HOOK,
    }
    
    if script:
        # Use custom script
        hook_file = hooks_dir / type
        hook_file.write_text(Path(script).read_text())
    else:
        # Use default script
        content = hook_scripts.get(type)
        if content:
            hook_file = hooks_dir / type
            hook_file.write_text(content)
        else:
            console.print(f"[red]✗ Unknown hook type: {type}[/red]")
            return
    
    # Make executable
    hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
    console.print(f"[green]✓ Hook installed: {type}[/green]")


PRE_COMMIT_HOOK = """#!/bin/sh
# Pre-commit hook

echo "Running pre-commit checks..."

# Run linting
if command -v ruff > /dev/null 2>&1; then
    echo "Linting with ruff..."
    ruff check .
    if [ $? -ne 0 ]; then
        echo "Linting failed. Please fix errors before committing."
        exit 1
    fi
fi

# Run formatting check
if command -v black > /dev/null 2>&1; then
    echo "Checking formatting with black..."
    black --check .
    if [ $? -ne 0 ]; then
        echo "Code not formatted. Run 'black .' to fix."
        exit 1
    fi
fi

# Run tests
if command -v pytest > /dev/null 2>&1; then
    echo "Running tests..."
    pytest
    if [ $? -ne 0 ]; then
        echo "Tests failed. Please fix before committing."
        exit 1
    fi
fi

echo "Pre-commit checks passed!"
exit 0
"""

PRE_PUSH_HOOK = """#!/bin/sh
# Pre-push hook

echo "Running pre-push checks..."

# Run full test suite
if command -v pytest > /dev/null 2>&1; then
    echo "Running full test suite..."
    pytest -v
    if [ $? -ne 0 ]; then
        echo "Tests failed. Push aborted."
        exit 1
    fi
fi

# Run type checking
if command -v mypy > /dev/null 2>&1; then
    echo "Type checking with mypy..."
    mypy .
    if [ $? -ne 0 ]; then
        echo "Type checking failed. Push aborted."
        exit 1
    fi
fi

echo "Pre-push checks passed!"
exit 0
"""

COMMIT_MSG_HOOK = """#!/bin/sh
# Commit message hook

commit_msg_file=$1
commit_msg=$(cat "$commit_msg_file")

# Check conventional commit format
if ! echo "$commit_msg" | grep -qE "^(feat|fix|docs|style|refactor|test|chore)(\\(.+\\))?: .+"; then
    echo "Invalid commit message format."
    echo "Use: <type>(<scope>): <message>"
    echo "Types: feat, fix, docs, style, refactor, test, chore"
    exit 1
fi

exit 0
"""

POST_COMMIT_HOOK = """#!/bin/sh
# Post-commit hook

echo "Commit successful!"

# Optional: Update changelog, send notification, etc.
"""

