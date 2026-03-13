# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-03-10

### 🔴 Critical Fixes
- **Default Branch Config Bug** — `push` and `init` now read `default_branch` from `~/.git-auto-config.json` instead of hardcoding `main`/`master`
- **Empty Commit Guard** — Prevents empty commits with Rich warning; handles `BadName` exception for brand new repos with no HEAD
- **Push Conflict Detection** — Detects rejected pushes due to diverged history, suggests `git-auto pull --rebase`
- **Offline / API Graceful Handling** — All GitHub API calls wrapped with `ConnectionError`/`Timeout` handling; no raw tracebacks

### 🟡 New Features
- **Safe Commit Flow** (`--safe` flag on `push`/`commit`)
  - Commits to `test/<branch>` automatically
  - Handles branch name collisions via `test/<branch>-{timestamp}` fallback
  - Auto-creates Pull Request with diff summary and review checklist
  - Configurable via `safe_mode`, `test_branch_prefix`, `auto_create_pr` settings
- **`git-auto undo`** — Undo last commit (soft/hard/force-push)
  - `--hard` with confirmation prompt
  - `--push` for soft reset + force push
  - `--yes` flag bypasses confirmation (CI-safe)
- **`git-auto release`** — Full release management
  - Reads version from `pyproject.toml` (canonical source)
  - Bumps patch/minor/major, syncs `__init__.py` + `setup.py`
  - Auto-generates changelog from conventional commits
  - Creates Git tag + GitHub release (with `--draft` option)

### 🟢 New Features
- **`git-auto doctor`** — System diagnostics
  - Checks: Git version, Python version, token validity, remote config, branch consistency, untracked files, safe mode
- **`git-auto pr`** — Standalone PR management
  - `git-auto pr "title"` — Create PR from current branch
  - `git-auto prs` — List pull requests
  - `git-auto merge-pr 42` — Merge PR (with `--squash`/`--rebase`)
  - `git-auto review-pr 42` — Open PR in browser

### New Modules
| Module | Purpose |
|--------|---------|
| `commands/safe_flow.py` | Safe commit flow |
| `commands/release.py` | Release management |
| `commands/doctor.py` | System diagnostics |
| `github_pr/pr_manager.py` | PR CRUD via GitHub API |

### New Config Options
- `safe_mode` — Enable safe commit flow by default (default: `false`)
- `test_branch_prefix` — Prefix for safe branches (default: `test`)
- `auto_create_pr` — Auto-create PR on safe push (default: `true`)
- `pr_base_branch` — Base branch for PRs (default: `main`)

### Testing
- 83 tests total (up from 42)
- 5 new test files: `test_undo.py`, `test_pr_manager.py`, `test_doctor.py`, `test_release.py`, `test_safe_flow.py`
- Zero regressions on existing test suite

---

## [1.1.0] - 2026-01-04

### Added
- **Interactive .gitignore Manager** 🎉
  - `git-auto ignore-manager` command
  - Browse all project files with ignore status
  - Select files to ignore with checkbox interface
  - Add patterns by type (folder, extension, file, custom)
  - Common presets (Python, Node.js, IDEs, Build artifacts, Logs)
  - Remove patterns from .gitignore
  - Clean already-tracked files from git
  - Preview changes before saving
  - Show current .gitignore patterns

### Enhanced
- Better file management workflow
- More user-friendly .gitignore creation
- Visual feedback for ignore status

---

## [1.0.0] - 2026-01-03

### Added
- GitHub authentication with secure keyring storage
- Repository creation and management
- Complete Git command automation
- Project scaffolding with multiple templates
- Interactive README, LICENSE, and .gitignore generators
- CI/CD workflow generation (GitHub Actions, GitLab CI)
- Git hooks management (pre-commit, pre-push, commit-msg)
- GitHub issue and PR template generation
- Collaboration features (add collaborators, branch protection)
- Repository backup and restore functionality
- Configuration system with persistent storage
- Repository statistics and analytics
- Support for Python 3.8+
- 30+ CLI commands
- Beautiful terminal output with Rich library

---

## [0.1.0] - Development

### Added
- Initial project structure
- Basic CLI framework
- Core functionality implementation
