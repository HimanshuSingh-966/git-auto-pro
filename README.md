# 🚀 Git-Auto Pro

**Complete Git + GitHub Automation CLI Tool**

Git-Auto Pro is a powerful command-line tool that automates your entire development workflow, from Git operations to GitHub repository management, project scaffolding, and CI/CD setup.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/pypi-git--auto--pro-orange.svg)](https://pypi.org/project/git-auto-pro/)

## 🆕 What's New in 2.7.0

- **`--json` output** — `issue list`, `issue view`, `prs`, `stats`, and `doctor` accept `--json` to emit machine-readable JSON for scripting (`git-auto issue list --json | jq ...`).
- **`--dry-run`** — preview destructive ops without running them: `git-auto undo --dry-run`, `push --force --dry-run`, `merge-pr 42 --dry-run`, `release patch --dry-run`.
- **`git-auto sync`** — pull with rebase then push, in one command.
- **Per-repo config** — drop a `.git-auto.json` at your repo root to override `~/.git-auto-config.json` (e.g. a different `default_branch` per project).
- **Shell completion** — `git-auto --install-completion` now installs bash/zsh/fish completion.
- **`GIT_AUTO_DEBUG`** — `export GIT_AUTO_DEBUG=1` now really enables debug logging to `~/.git-auto.log` (it was documented before but not implemented).
- **Stronger `doctor`** — reports token scopes (warns if `repo`/`workflow` are missing), checks upstream tracking, and shows ahead/behind; supports `--json`.

See the [CHANGELOG](CHANGELOG.md) for the full list.

## 🆕 What's New in 2.6.0

- **Pagination** — `issue list` and `prs` now follow GitHub's `Link` header, so `--limit 500` and large repos no longer silently cap at 100.
- **Rate-limit handling** — 429 / rate-limited-403 responses report the reset time and `Retry-After`; you get a heads-up when your API budget runs low.
- **Safe URLs** — repo/owner/branch names with special characters (`#`, `?`, spaces) are now URL-encoded, fixing broken requests and closing a path-injection gap.
- **Faster** — the authenticated session and current user are cached per invocation, cutting the redundant `GET /user` call every GitHub command used to make.
- **Consistent failures** — `issue create` no longer raises on API errors; it returns empty like the other issue commands.
- **Safer token storage** — warns if the fallback token file can't be locked to `0o600`, and `logout` is honest when the keyring entry can't be removed.

See the [CHANGELOG](CHANGELOG.md) for the full list.

## 🆕 What's New in 2.5.0

- **Org/fork repo support** — GitHub commands (`issue`, `pr`, `prs`, `merge-pr`, `review-pr`, `collab`, `protect`) now detect the repository **owner** from your `origin` remote instead of assuming it's your own. They work on organization, fork, and collaborator repos. Pass `--repo owner/name` to target any repo explicitly.
- **`git-auto new` honors `default_branch`** — no longer hardcodes `main`; aligns the local branch to your configured default before pushing.
- **Real backups** — `git-auto backup` now archives the full `.git` (including `objects/`), so `git-auto restore` actually brings back your history.
- **Portable generated hooks** — `pre-commit`/`pre-push` hooks are now POSIX-`sh` safe and no longer break on `dash` (`/bin/sh` on Ubuntu/Debian) when ruff/black/pytest aren't installed.
- **Honest PR feedback** — `git-auto pr` no longer claims "✓ Reviewers requested" when the API rejected the request; it reports the real HTTP status.
- **Tougher network handling** — `issue close`/`update` and all PR ops now handle connection errors and timeouts gracefully instead of dumping a traceback.
- **Modern GitHub auth** — `Bearer` tokens, current API media type, and version header; deprecated preview headers removed.

See the [CHANGELOG](CHANGELOG.md) for the full list.

## ✨ Features

### 🔐 GitHub Authentication
- Secure token storage using OS-level keyring (Keychain/Credential Manager/Secret Service)
- Token validation via GitHub API
- Support for Personal Access Tokens

### 📦 Repository Management
- Create public/private repositories
- Set descriptions, topics, and homepage URLs
- Automatic remote configuration
- Repository statistics and analytics

### 🎬 Project Creation
- Complete project scaffolding with one command
- Multiple language templates (Python, Node.js, C++, Rust, Go, Web)
- Automatic Git initialization
- GitHub repository creation and push

### 💻 Git Operations
- Simplified Git commands with intuitive syntax
- Branch management (create, switch, delete, list)
- Stash operations
- Merge with options (no-ff, squash)
- Clone with shallow copy support
- Interactive status and log display

### 📝 Generators
- **README.md**: Professional, customizable README templates
- **LICENSE**: Multiple license types (MIT, Apache, GPL, BSD, etc.)
- **.gitignore**: Language-specific templates
- **Project Templates**: Full project structures for various languages

### ⚙️ CI/CD Workflows
- GitHub Actions workflows (CI, CD, testing, release)
- GitLab CI configuration
- Pre-configured for Python projects
- Extensible to other platforms

### 🪝 Git Hooks
- Pre-commit: Linting, formatting, testing
- Pre-push: Full test suite, type checking
- Commit-msg: Conventional commit validation
- Post-commit: Custom notifications

### 📋 GitHub Templates
- Issue templates (bug reports, feature requests)
- Pull request templates
- CONTRIBUTING.md generation
- Standardized collaboration workflows

### 🐛 GitHub Issues
- Create issues with labels and assignees
- List and filter issues (open/closed/all)
- View issue details
- Close issues with comments
- Update issue properties

### 🛡️ Safe Commit Flow (v2.0)
- Push to test branches automatically (`--safe` flag)
- Auto-create Pull Requests with review checklists
- Branch collision detection with timestamp fallback
- Configurable via settings (`safe_mode`, `test_branch_prefix`)

### ⏪ Undo & Release (v2.0)
- `git-auto undo` — Soft/hard reset with confirmation prompts
- `git-auto release` — Tag, bump version, push, create GitHub releases
- Canonical version source from `pyproject.toml`

### 🩺 Diagnostics (v2.0)
- `git-auto doctor` — Git, Python, token, remote, branch consistency checks

### 📋 Pull Request Management (v2.0)
- Create, list, merge, and review PRs from CLI
- Supports `--draft`, `--reviewer`, `--label`, `--squash`, `--rebase`

### 👥 Collaboration
- Add collaborators to repositories
- Branch protection rules
- Permission management

### 💾 Backup & Restore
- Create repository snapshots
- Compress and archive entire projects
- Restore from backups

### ⚙️ Configuration
- Persistent configuration storage
- Customizable defaults (branch names, commit messages, licenses)
- Per-user settings

## 📦 Installation

### From PyPI
```bash
pip install git-auto-pro
```

### From Source
```bash
git clone https://github.com/HimanshuSingh-966/git-auto-pro.git
cd git-auto-pro
pip install -e .
```

### Requirements
- Python 3.8 or higher
- Git installed on your system
- GitHub Personal Access Token (for GitHub features)

## 🚀 Quick Start

### 1. Login to GitHub
```bash
git-auto login
# Enter your GitHub Personal Access Token when prompted
```

**Creating a Token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `workflow`, `admin:org`
4. Copy the token

### 2. Create a New Project
```bash
git-auto new my-awesome-project
# This will:
# - Create project directory
# - Generate README, LICENSE, .gitignore
# - Initialize Git repository
# - Create GitHub repository
# - Push initial commit
```

### 3. Work with Git
```bash
# Stage and commit
git-auto add --all
git-auto commit "Add new feature"

# Or do it all at once
git-auto push "Add new feature" --branch main

# Check status
git-auto status

# View history
git-auto log --limit 5 --graph
```

## 📖 Command Reference

### Authentication
```bash
git-auto login                          # Login to GitHub
git-auto login --token YOUR_TOKEN       # Login with token directly
```

### Repository Management
```bash
git-auto create-repo myrepo                    # Create public repo
git-auto create-repo myrepo --private          # Create private repo
git-auto create-repo myrepo \
  --description "My project" \
  --homepage "https://example.com" \
  --topics "python,cli,automation"
```

### Project Creation
```bash
git-auto new myproject                         # Interactive mode
git-auto new myproject --template python       # With template
git-auto new myproject --private               # Private repo
git-auto new myproject --no-github             # Skip GitHub
```

### Git Operations
```bash
# Initialize
git-auto init                                  # Initialize Git
git-auto init --connect URL                    # Initialize and connect

# Basic commands
git-auto add file1.py file2.py                # Stage specific files
git-auto add --all                             # Stage all files
git-auto commit "message"                      # Commit
git-auto commit "message" --conventional       # Conventional commit
git-auto commit "message" --amend              # Amend last commit
git-auto push                                  # Push
git-auto push "message"                        # Add, commit, and push
git-auto push --force                          # Force push
git-auto push --force --dry-run                # Preview force push without doing it
git-auto push --safe "message"                 # Safe commit flow (test branch + PR)
git-auto sync                                  # Pull --rebase then push (one command)
git-auto pull                                  # Pull (merge strategy)
git-auto pull --rebase                         # Pull with rebase
git-auto pull --no-rebase                      # Pull with merge (default)
git-auto pull --ff-only                        # Only fast-forward
git-auto pull -b main --rebase                 # Pull specific branch with rebase

# Status and history
git-auto status                                # Formatted status
git-auto status --short                        # Short format
git-auto log                                   # Show commits
git-auto log --limit 20                        # Show 20 commits
git-auto log --oneline                         # One line per commit
git-auto log --graph                           # With graph

# Branches
git-auto branch                                # List branches
git-auto branch newbranch                      # Create branch
git-auto branch --list                         # List all branches
git-auto branch --remote                       # List remote branches
git-auto switch develop                        # Switch branch
git-auto switch -c feature                     # Create and switch
git-auto delete-branch feature                 # Delete branch
git-auto delete-branch feature --force         # Force delete

# Stash
git-auto stash                                 # Stash changes
git-auto stash --message "WIP"                 # Stash with message
git-auto stash --list                          # List stashes
git-auto stash-apply                           # Apply latest stash
git-auto stash-apply --index 1                 # Apply specific stash
git-auto stash-apply --pop                     # Apply and remove

# Merge
git-auto merge develop                         # Merge branch
git-auto merge develop --no-ff                 # No fast-forward
git-auto merge develop --squash                # Squash merge

# Clone
git-auto clone URL                             # Clone repository
git-auto clone URL --dir mydir                 # Clone to directory
git-auto clone URL --depth 1                   # Shallow clone

# Statistics
git-auto stats                                 # Basic stats
git-auto stats --detailed                      # Detailed stats
```

### Generators
```bash
# README
git-auto readme                                # Interactive mode
git-auto readme --output docs/README.md        # Custom output

# License
git-auto license                               # Interactive selection
git-auto license --type MIT                    # Specific license
git-auto license --author "Your Name" --year 2024

# .gitignore
git-auto ignore                                # Interactive selection
git-auto ignore --template python              # Python template

# Templates
git-auto template python                       # Python project
git-auto template node                         # Node.js project
git-auto template cpp                          # C++ project
git-auto template web                          # Web project
git-auto template rust                         # Rust project
git-auto template go                           # Go project
git-auto ignore-manager                        # Launch interactive manager

# Features:
# - Browse all project files
# - Select files to ignore with checkboxes
# - Add patterns by type (folder, extension, file)
# - Use common presets (Python, Node, etc.)
# - View ignore status of all files
# - Clean already-tracked files
```

### Workflows & Hooks
```bash
# CI/CD Workflows
git-auto workflow ci                           # GitHub Actions CI
git-auto workflow test                         # Test workflow
git-auto workflow cd                           # Deployment workflow
git-auto workflow release                      # Release workflow
git-auto workflow ci --platform gitlab         # GitLab CI

# Git Hooks
git-auto hook pre-commit                       # Pre-commit hook
git-auto hook pre-push                         # Pre-push hook
git-auto hook commit-msg                       # Commit message hook
git-auto hook post-commit                      # Post-commit hook
git-auto hook pre-commit --script custom.sh    # Custom script

# GitHub Templates
git-auto templates issue                       # Issue templates
git-auto templates pr                          # PR template
git-auto templates contributing                # CONTRIBUTING.md
```

### GitHub Issues
```bash
# Create issues
git-auto issue create                          # Interactive mode
git-auto issue create --title "Bug fix" --body "Description"
git-auto issue create -t "Feature" -l "enhancement,priority"

# List issues
git-auto issue list                            # List open issues
git-auto issue list --state closed             # List closed issues
git-auto issue list --state all                # List all issues
git-auto issue list --labels bug               # Filter by label
git-auto issue list --assignee username        # Filter by assignee
git-auto issue list --json                     # Emit JSON for scripting

# View and manage issues
git-auto issue view 42                         # View issue #42
git-auto issue close 42                        # Close issue
git-auto issue close 42 --comment "Fixed"      # Close with comment
git-auto issue update 42 --title "New title"   # Update issue
git-auto issue update 42 --state closed        # Change state
```

> **Note:** Add `--repo owner/name` to target any repository you have access to.
> Without it, the owner is detected from your `origin` remote (works for org/fork repos).

### Collaboration
```bash
# Add collaborators
git-auto collab username                       # Add to current repo (owner auto-detected)
git-auto collab username --repo owner/name     # Target any repo you have access to
git-auto collab username --permission admin    # With permission level

# Branch protection
git-auto protect main                          # Protect main branch
git-auto protect develop --repo owner/name     # Protect a branch in a specific repo
```

> **Note:** The owner is detected from your `origin` remote, so these work for
> organization, fork, and collaborator repos — not just repos you own. Use
> `--repo owner/name` to override.

### Backup & Restore
```bash
git-auto backup                                # Create backup
git-auto backup --output backup.tar.gz         # Custom filename
git-auto restore backup.tar.gz                 # Restore from backup
```

### Configuration
```bash
git-auto config set default_branch develop     # Set default branch
git-auto config set default_license Apache-2.0 # Set default license
git-auto config set conventional_commits true  # Enable conventional commits
git-auto config get default_branch             # Get value
git-auto config list                           # List all config
git-auto config reset --yes                    # Reset to defaults
```

### Utility
```bash
git-auto version                               # Show version
git-auto --help                                # Show help
git-auto COMMAND --help                        # Command-specific help
```

### Undo
```bash
git-auto undo                                  # Soft reset (keep changes staged)
git-auto undo --hard --yes                     # Hard reset (discard changes)
git-auto undo --push --yes                     # Soft reset + force push
git-auto undo --dry-run                        # Preview without changing history
```

### Release
```bash
git-auto release patch                         # Bump patch version
git-auto release minor                         # Bump minor version
git-auto release major                         # Bump major version
git-auto release 2.1.0                         # Set exact version
git-auto release patch --draft                 # Create draft release
git-auto release minor --notes "Custom notes"  # With release notes
git-auto release patch --dry-run               # Preview the release without doing anything
```

### Doctor
```bash
git-auto doctor                                # Run all diagnostics
git-auto doctor --json                         # Emit diagnostics as JSON
```

### Pull Requests
```bash
git-auto pr "Fix login bug"                    # Create PR from current branch
git-auto pr "Feature" --draft                  # Create draft PR
git-auto pr "Fix" --reviewer user1 --label bug # With reviewer and label
git-auto prs                                   # List open PRs
git-auto prs --state closed                    # List closed PRs
git-auto prs --json                            # Emit JSON for scripting
git-auto merge-pr 42                           # Merge PR
git-auto merge-pr 42 --squash                  # Squash merge
git-auto merge-pr 42 --dry-run                 # Preview the merge without doing it
git-auto review-pr 42                          # Open PR in browser
```

> **Note:** PR commands detect the owner from your `origin` remote, so they work
> for organization and fork repos. Pass `--repo owner/name` to override.

## 🎯 Use Cases

### Starting a New Python Project
```bash
# Create and setup everything
git-auto new my-python-app --template python --private

# Navigate and start coding
cd my-python-app
# Project structure is ready with:
# - src/ directory
# - tests/ directory
# - requirements.txt
# - README.md, LICENSE, .gitignore
# - Git initialized and pushed to GitHub
```

### Daily Development Workflow
```bash
# Morning: Start new feature
git-auto switch -c feature/new-login develop
git-auto pull

# During development
git-auto status
git-auto push "Implement login form"
git-auto push "Add validation"

# Evening: Merge to develop
git-auto switch develop
git-auto merge feature/new-login
git-auto push
```

### Setting Up CI/CD
```bash
# Generate GitHub Actions workflows
git-auto workflow ci
git-auto workflow test
git-auto workflow cd

# Setup pre-commit hooks
git-auto hook pre-commit
git-auto hook pre-push

# Commit and push
git-auto push "Setup CI/CD pipeline"
```

### Collaborative Development
```bash
# Setup branch protection
git-auto protect main
git-auto protect develop

# Add team members
git-auto collab teammate1 --permission push
git-auto collab teammate2 --permission admin

# Generate templates
git-auto templates issue
git-auto templates pr
git-auto templates contributing
```

## 🔧 Configuration Options

Configuration is stored in `~/.git-auto-config.json`.

For per-project overrides, add a `.git-auto.json` at your repository root. It
takes precedence over the user config (which in turn overrides the built-in
defaults). Useful for giving one project a different `default_branch`,
`safe_mode`, or `pr_base_branch` without changing your global settings.

Available options:
- `default_branch`: Default branch name (default: "main")
- `default_commit_message`: Default commit message
- `default_license`: Default license type (default: "MIT")
- `default_project_type`: Default project template
- `auto_push`: Automatically push after commit
- `conventional_commits`: Enforce conventional commits
- `editor`: Default text editor
- `git_user_name`: Git username
- `git_user_email`: Git email
- `safe_mode`: Enable safe commit flow by default (default: `false`)
- `test_branch_prefix`: Prefix for test branches (default: `test`)
- `auto_create_pr`: Auto-create PR on safe push (default: `true`)
- `pr_base_branch`: Base branch for PRs (default: `main`)

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](https://github.com/HimanshuSingh-966/git-auto-pro/blob/main/CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git-auto switch -c feature/amazing`)
3. Commit your changes (`git-auto commit "Add amazing feature"`)
4. Push to the branch (`git-auto push`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/HimanshuSingh-966/git-auto-pro/blob/main/LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for the CLI
- Uses [GitPython](https://gitpython.readthedocs.io/) for Git operations
- Powered by [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- Token storage via [keyring](https://github.com/jaraco/keyring)

## 📞 Support

- 🐛 Report bugs: [GitHub Issues](https://github.com/HimanshuSingh-966/git-auto-pro/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/HimanshuSingh-966/git-auto-pro/discussions)
- 📧 Email: choudharyhimanshusingh966@gmail.com

## 🗺️ Roadmap

- [ ] VS Code extension integration
- [ ] GitLab support
- [ ] Bitbucket support
- [ ] Interactive TUI mode
- [ ] Plugin system for custom commands
- [ ] Team workspace management
- [ ] Advanced analytics dashboard

---

**Made with ❤️ by developers, for developers**

⭐ Star this repo if you find it useful!
