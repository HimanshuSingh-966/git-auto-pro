# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.7.1] - 2026-08-01

### 📚 Documentation & Test Quality (Patch Release)

This release contains no new user-facing features — it corrects test isolation bugs and brings the documentation back in sync with the 2.7.0 implementation.

#### 🐛 Fixes
- **`test_cli.py` config isolation** — `TestConfigCommands` was writing test keys to the real `~/.git-auto-config.json`. Now monkeypatched to a temporary file; verified no side effects on your actual config.
- **`.gitignore` cleanup** — removed stray `"""` from the last line (accidental paste).
- **`build.sh` ordering** — moved format/lint steps before `pytest` so the build verifies the code that was actually tested, not code rewritten by `ruff --fix` afterward.

#### 🧪 Testing
- **Added `test_pr_manager.py`** — 9 tests covering PR create/list/merge/get/review. The PR manager had zero test coverage despite the CHANGELOG claiming it existed since 2.4.0.
- **Dropped `test_undo.py`** — it was a 0-line placeholder; undo is already covered by the `--dry-run` tests in `test_tier3.py`.
- **127 tests total** (up from 118).

#### 📄 Documentation
- **Rewrote `CONTRIBUTING.md`** — removed the npm/Jest/JavaScript boilerplate that told contributors to `npm install` and write Jest tests; now tailored to this Python/pytest project, the Makefile, and the test-isolation rule.
- **Updated `SETUP_GUIDE.md`** — added `commands/`, `github_pr/`, `gitignore_manager.py`, `backup.py`, `logging_setup.py`, and the full 16-file test list to the project-structure tree (was showing only 4 tests, pre-v2.0).
- **Completed `docs/api.md`** — covered all ~43 commands with correct options (`--json`, `--dry-run`, `--repo owner/name`, `sync`, `doctor`, `undo`, `release`, etc.). It was missing ~30 commands.
- **Fixed `docs/examples.md`** — removed the invalid `issue update --assignees` (that command has no `--assignees`; assignees are set at `issue create` via `-a`).
- **Fixed `docs/usage.md` release section** — replaced the manual `git tag v1.1.0 && git push --tags` workflow with the implemented `git-auto release` command, which handles version-file updates, commit, tag, push, and GitHub release creation in one step.

---

## [2.7.0] - 2026-07-27

### ✨ New Features
- **`--json` output** — `issue list`, `issue view`, `prs`, `stats`, and `doctor` now accept `--json` to emit machine-readable JSON (via `json.dumps(..., indent=2)`) instead of Rich tables/panels. Makes the tool scriptable from `jq`, makefiles, and CI.
- **`--dry-run`** — destructive operations now support `--dry-run` to print the planned action without executing: `undo`, `push` (incl. `--force`), `merge-pr`, `release`, and the ignore-manager's `clean-ignored-files`.
- **`git-auto sync`** — new command that pulls with rebase then pushes the current branch, the daily-workflow one-liner.
- **Per-repo config** — a repo-local `.git-auto.json` at the repository root now overrides `~/.git-auto-config.json` (which still overrides the defaults). Precedence: defaults < user < repo.
- **Shell completion** — enabled (`add_completion=True`); run `git-auto --install-completion` to install bash/zsh/fish completion.
- **`GIT_AUTO_DEBUG` logging** — the debug mode documented in `troubleshooting.md` is now actually implemented. `export GIT_AUTO_DEBUG=1` enables debug logging to `~/.git-auto.log` (and stderr). See `git_auto_pro/logging_setup.py`.
- **Stronger `doctor`** — now reports token scopes (warns if `repo`/`workflow` are missing), checks upstream tracking, and shows ahead/behind vs upstream. Modernized the token check to `Bearer` auth. `doctor` also supports `--json`.

### 🐛 Fixes
- **`release` owner detection** — `create_release` now resolves the repo owner from the `origin` remote (via `resolve_repo_ref` + `_api_url`) instead of assuming the authenticated user, so GitHub releases are created against the correct repo for org/fork projects.

### 🧪 Testing
- 118 tests total (up from 110)
- New `test_tier3.py` covering per-repo config precedence, `stats --json`, `--dry-run` no-ops for `undo`/`release`/`git-sync`, and doctor token-scope parsing (ok + missing-workflow warn)

---

## [2.6.0] - 2026-07-26

### 🛡️ Robustness & API Hardening
- **Pagination** — `issue list` and `prs` now follow the GitHub `Link: rel="next"` header instead of issuing a single request capped at GitHub's 100-per-page ceiling. `--limit` values above 100 (or large repos) are no longer silently truncated.
- **Rate-limit awareness** — 429 responses and 403-with-`X-RateLimit-Remaining: 0` are detected and reported with the reset time / `Retry-After`. Successful responses also print a proactive warning when the remaining budget is low (≤ 5).
- **URL-encoding** — all GitHub path parameters (owner, repo, username, branch) are now percent-encoded via a shared `_api_url()` helper. Branch/repo names containing `#`, `?`, spaces, or `/` no longer break the request or risk path-injection.
- **Cached session + current user** — the authenticated `requests.Session` and `GET /user` result are cached per process and invalidated on login/logout/token changes, eliminating the redundant `GET /user` round-trip every GitHub operation used to make.
- **Consistent error contract** — `issue create` now returns `{}` on HTTP failure instead of re-raising, matching `list`/`get`/`close`/`update`. (`create_pull_request` still raises, since the safe-push flow depends on either a number-bearing dict or an exception.)

### 🔐 Token Storage
- **`chmod` warning** — if setting `0o600` on the fallback token file fails, a warning is now printed (previously silently swallowed), since the plaintext token could be readable by other users.
- **Honest `logout`** — `clear_stored_token` now warns if the keyring entry could not be removed (it may still be stored) rather than reporting success; it also reports when there was no token to clear.

### 🧪 Testing
- 110 tests total (up from 89)
- New `test_github_robustness.py` covering `_api_url` encoding, `_next_link`, `_paginated_get` (follows `Link`, respects limit, empty/single page), `_is_rate_limited`, and auth-cache invalidation
- Autouse fixture clears the auth cache between tests to prevent cross-test leakage

---

## [2.5.0] - 2026-07-26

### 🔴 Critical Fixes
- **Repository owner now detected from the remote URL** — `issue`, `pr`, `prs`, `merge-pr`, `review-pr`, `collab`, and `protect` previously assumed the repository belonged to the authenticated user (`repos/<you>/<repo>`), so they 404'd on organization, fork, or collaborator repos. The owner is now parsed from the `origin` remote (HTTPS, scp-style SSH `git@github.com:owner/repo`, `ssh://`, and `git://` forms). `--repo owner/name` is supported on all of these commands; a bare `--repo name` keeps the legacy behavior (paired with your login).
- **`git-auto new` respects `default_branch`** — project creation no longer hardcodes `main`; it reads the configured default branch and aligns the local branch (`git branch -M`) before pushing, so it no longer fails when git's initial branch is `master`.
- **Backups now preserve history** — `backup` archives the entire `.git` directory (including `objects/`). Previously only `.git/{config,HEAD,refs,hooks}` were archived, leaving refs pointing at missing objects, so a restored repo had no history. `restore` now uses the `filter="data"` extraction guard on Python 3.12+.
- **Generated git hooks are POSIX-`sh` safe** — `pre-commit`/`pre-push` hooks used the bash-only `&>` redirect, which `/bin/sh` (dash on Ubuntu/Debian) parses as `&` (background) + `> /dev/null`. This made the `command -v <tool>` guard always pass, so the hook ran the (missing) tool and failed, blocking commits on systems without ruff/black/pytest installed. Replaced with the POSIX `> /dev/null 2>&1` form.
- **PR reviewers/labels report the real outcome** — `pr` no longer prints `✓ Reviewers requested` / `✓ Labels added` when the API rejected the request (e.g. 422). The sub-requests now call `raise_for_status()` and report the actual HTTP status on failure.
- **`close_issue` / `update_issue` network handling** — both now catch `ConnectionError`/`Timeout` (previously only `HTTPError` was caught, so a transient network error crashed with a raw traceback). All requests have `timeout=10`. The closing comment is now best-effort — a network error on the comment no longer aborts the actual close.
- **Accurate `merge-pr` diagnostics** — 405 now reports "not mergeable (pending/failed checks, missing reviews, draft, or branch protection)" and 409 reports "merge conflicts or head branch changed". The previous messages were swapped.

### 🛠️ Changed
- **Modernized GitHub auth** — switched from the legacy `Authorization: token <PAT>` scheme and `application/vnd.github.v3+json` media type to `Authorization: Bearer <PAT>`, `application/vnd.github+json`, and the `X-GitHub-Api-Version: 2022-11-28` header. Removed the deprecated `mercy-preview` (topics) and `luke-cage-preview` (branch protection) preview media types.
- **Removed dead code** — deleted an accidental ~190-line duplicate of the `github_templates` module that had been pasted into `scaffolding/hooks.py` (it was never imported; `cli.py` uses the real `github_templates.py`). `hooks.py` shrank from 331 to 138 lines.
- **Reduced redundant API calls** — GitHub operations no longer make a separate `GET /user` round-trip solely to build repo URLs when the owner is detected from the remote.

### 🧪 Testing
- 89 tests total (up from 70)
- 3 new test files: `test_github_remote.py` (remote URL parsing + owner resolution), `test_hooks.py` (POSIX-`sh` portability incl. live `dash` execution), `test_backup.py` (backup/restore round-trip proving history survives)
- Zero regressions on the existing suite

---

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
