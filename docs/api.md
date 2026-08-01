# API Reference - Git-Auto Pro

Complete reference for all `git-auto` commands, arguments, and options.

## Command Structure

```
git-auto [COMMAND] [ARGUMENTS] [OPTIONS]
```

Global notes:

- Most GitHub commands accept `--repo owner/name` to target a specific
  repository. Without it, the owner/repo is detected from your `origin`
  remote (works for organization, fork, and collaborator repos).
- List/view commands (`issue list`, `issue view`, `prs`, `stats`, `doctor`)
  accept `--json` to emit machine-readable JSON.
- Destructive commands (`undo`, `push --force`, `merge-pr`, `release`,
  ignore-manager clean) accept `--dry-run` to preview without executing.

## Authentication

### `git-auto login`

Login to GitHub using a Personal Access Token (stored in the OS keyring, or a
file fallback).

**Options:**
- `--token, -t TEXT`: Provide the token directly (otherwise prompted securely)

```bash
git-auto login
git-auto login --token ghp_xxxxxxxxxxxx
```

### `git-auto logout`

Clear the stored GitHub token.

**Options:**
- `--yes, -y`: Skip the confirmation prompt

## Repository Management

### `git-auto create-repo NAME`

Create a new GitHub repository under your account.

**Arguments:** `NAME` (required)

**Options:**
- `--private, -p`: Create a private repository
- `--description, -d TEXT`: Repository description
- `--homepage, -h TEXT`: Homepage URL
- `--topics, -t TEXT`: Comma-separated topics
- `--auto-init`: Initialize with a README

```bash
git-auto create-repo myproject --private --description "My project" --topics "python,cli"
```

### `git-auto init`

Initialize a Git repository in the current directory.

**Options:**
- `--connect, -c URL`: Also configure the `origin` remote (adds or updates it)

```bash
git-auto init --connect https://github.com/user/repo.git
```

## Project Creation

### `git-auto new PROJECT_NAME`

Scaffold a complete project: template files, README, LICENSE, .gitignore,
`git init`, initial commit, and (unless skipped) GitHub repo creation + push.
Respects your configured `default_branch`.

**Arguments:** `PROJECT_NAME` (required)

**Options:**
- `--template, -t TEXT`: Project template (`python`, `node`, `cpp`, `rust`, `go`, `web`)
- `--private, -p`: Create a private GitHub repo
- `--no-github`: Skip GitHub repository creation

```bash
git-auto new myproject --template python --private
```

## Git Operations

### `git-auto add [FILES]`

Stage files for commit.

**Options:** `--all, -A` — stage all changes (default when no files given)

### `git-auto commit [MESSAGE]`

Commit staged changes.

**Options:**
- `--conventional, -c`: Interactive conventional-commit prefix
- `--amend`: Amend the previous commit
- `--safe`: Use the safe commit flow (commit to a `test/...` branch + PR)

### `git-auto push [MESSAGE]`

Push to remote. With `MESSAGE`, also stages and commits first. The target
branch defaults to the configured `default_branch`.

**Options:**
- `--branch, -b TEXT`: Branch to push
- `--force, -f`: Force push
- `--safe`: Safe commit flow (requires a message)
- `--dry-run`: Preview without executing

### `git-auto pull`

Pull changes from remote.

**Options:**
- `--branch, -b TEXT`: Branch to pull
- `--rebase, -r`: Rebase instead of merge
- `--no-rebase`: Merge (default)
- `--ff-only`: Only allow fast-forward

### `git-auto sync`

Pull with rebase then push the current branch, in one command.

**Options:** `--dry-run` — preview without executing

### `git-auto status`

Show working-tree status.

**Options:** `--short, -s` — short format

### `git-auto log`

Show commit history.

**Options:**
- `--limit, -n INT`: Number of commits (default: 10)
- `--oneline`: One line per commit
- `--graph, -g`: Show the commit graph

## Branches

### `git-auto branch [NAME]`

Create a branch, or list branches when `NAME` is omitted.

**Options:**
- `--list, -l`: List all branches
- `--remote, -r`: List remote branches

### `git-auto switch NAME`

Switch to a branch.

**Options:** `--create, -c` — create the branch if it doesn't exist

### `git-auto delete-branch NAME`

Delete a branch.

**Options:** `--force, -f` — force delete (`-D`)

## Stash

### `git-auto stash`

Stash uncommitted changes.

**Options:**
- `--message, -m TEXT`: Stash message
- `--list, -l`: List all stashes

### `git-auto stash-apply`

Apply a stash.

**Options:**
- `--index, -i INT`: Stash index (default: 0)
- `--pop, -p`: Apply and drop the stash

## Merge & Clone

### `git-auto merge BRANCH`

Merge a branch into the current one.

**Options:**
- `--no-ff`: No fast-forward
- `--squash`: Squash merge

### `git-auto clone URL`

Clone a repository.

**Options:**
- `--dir, -d PATH`: Target directory
- `--depth INT`: Shallow clone depth

## Statistics

### `git-auto stats`

Show repository statistics (commits, branches, contributors, current branch).

**Options:**
- `--detailed, -d`: Include a top-contributors table
- `--json`: Emit JSON

## Generators

### `git-auto readme`

Generate a README.md.

**Options:**
- `--interactive, -i`: Interactive mode (default: true)
- `--output, -o PATH`: Output file (default: `README.md`)

### `git-auto license`

Generate a LICENSE file.

**Options:**
- `--type, -t TEXT`: License type (MIT, Apache-2.0, GPL-3.0, BSD-3-Clause, ...)
- `--author, -a TEXT`: Author name
- `--year, -y INT`: Copyright year

### `git-auto ignore`

Generate a `.gitignore`.

**Options:** `--template, -t TEXT` — language template (`python`, `node`, ...)

### `git-auto template TYPE`

Generate a project template structure in a directory.

**Arguments:** `TYPE` — `python`, `node`, `cpp`, `rust`, `go`, or `web`

**Options:** `--output, -o PATH` — output directory

### `git-auto ignore-manager`

Launch the interactive .gitignore manager (browse files, presets, clean
tracked files). No options.

## Workflows & Hooks

### `git-auto workflow TYPE`

Generate CI/CD workflow files.

**Arguments:** `TYPE` — `ci`, `test`, `cd`, or `release`

**Options:** `--platform, -p TEXT` — `github` (default) or `gitlab`

### `git-auto hook TYPE`

Install a Git hook (POSIX-sh compatible).

**Arguments:** `TYPE` — `pre-commit`, `pre-push`, `commit-msg`, or `post-commit`

**Options:** `--script, -s PATH` — use a custom script instead of the built-in

### `git-auto templates TYPE`

Generate GitHub templates.

**Arguments:** `TYPE` — `issue`, `pr`, or `contributing`

## GitHub Issues

All issue commands accept `--repo, -r owner/name` (auto-detected otherwise).

### `git-auto issue create`

Create an issue (interactive prompts if title omitted).

**Options:**
- `--title, -t TEXT`
- `--body, -b TEXT`
- `--labels, -l TEXT`: Comma-separated labels
- `--assignees, -a TEXT`: Comma-separated assignees
- `--repo, -r TEXT`

### `git-auto issue list`

List issues.

**Options:**
- `--state, -s TEXT`: `open` (default), `closed`, or `all`
- `--labels, -l TEXT`: Filter by label
- `--assignee, -a TEXT`: Filter by assignee
- `--limit, -n INT`: Max results (default: 30; paginated past 100)
- `--json`: Emit JSON
- `--repo, -r TEXT`

### `git-auto issue view NUMBER`

View a single issue.

**Options:** `--repo, -r TEXT`, `--json`

### `git-auto issue close NUMBER`

Close an issue.

**Options:** `--comment, -c TEXT` (posted before closing), `--repo, -r TEXT`

### `git-auto issue update NUMBER`

Update an issue's fields.

**Options:** `--title, -t TEXT`, `--body, -b TEXT`, `--state, -s TEXT` (`open`/`closed`), `--labels, -l TEXT`, `--repo, -r TEXT`

## Pull Requests

### `git-auto pr TITLE`

Create a pull request from the current branch (requires being on a
non-base branch).

**Options:**
- `--draft`: Create a draft PR
- `--reviewer, -r TEXT`: Request reviewer(s) (repeatable)
- `--label, -l TEXT`: Add label(s) (repeatable)
- `--base, -b TEXT`: Base branch (default: configured `pr_base_branch`)

### `git-auto prs`

List pull requests.

**Options:**
- `--state, -s TEXT`: `open` (default), `closed`, or `all`
- `--limit, -n INT`: Max results (default: 30; paginated past 100)
- `--json`: Emit JSON

### `git-auto merge-pr NUMBER`

Merge a pull request.

**Options:**
- `--squash`: Squash merge
- `--rebase`: Rebase merge
- `--dry-run`: Preview without merging

### `git-auto review-pr NUMBER`

Open the PR in your browser.

## Collaboration

### `git-auto collab USERNAME`

Add a collaborator to a repository.

**Options:**
- `--repo, -r owner/name`: Target repo (auto-detected otherwise)
- `--permission, -p TEXT`: `pull`, `push` (default), `admin`, `maintain`, `triage`

### `git-auto protect [BRANCH]`

Enable branch protection (requires 1 approving review).

**Arguments:** `BRANCH` (default: `main`)

**Options:** `--repo, -r owner/name`

## Backup & Restore

### `git-auto backup`

Archive the working tree **and the full `.git`** (including objects) to a
`.tar.gz`, so history survives a restore.

**Options:** `--output, -o PATH` — output file (default: timestamped name)

### `git-auto restore BACKUP_PATH`

Extract a backup into `./restored/`.

## Undo & Release

### `git-auto undo`

Undo the last commit.

**Options:**
- `--hard`: Hard reset (discards changes; confirmation required)
- `--push`: Soft reset then force-push (confirmation required)
- `--yes, -y`: Skip confirmation
- `--dry-run`: Preview without changing history

### `git-auto release VERSION`

Create a release: bump version (in `pyproject.toml` + `setup.py` +
`__init__.py`), commit, tag, push, and create a GitHub release against the
repo detected from `origin`.

**Arguments:** `VERSION` — `patch`, `minor`, `major`, or an exact `X.Y.Z`

**Options:**
- `--draft`: Create a draft GitHub release
- `--notes, -n TEXT`: Custom release notes (otherwise generated from commits)
- `--dry-run`: Print the full plan without executing

## Diagnostics

### `git-auto doctor`

Run system diagnostics: git/python versions, token validity **and scopes**
(`repo`/`workflow`), remote config, branch consistency, upstream tracking
with ahead/behind, untracked/uncommitted files, safe mode.

**Options:** `--json` — emit results as JSON

## Configuration

### `git-auto config set KEY VALUE`

Set a value in the user config (`~/.git-auto-config.json`).

### `git-auto config get KEY`

Print a configuration value.

### `git-auto config list`

List all configuration values.

### `git-auto config reset`

Reset the user config to defaults.

**Options:** `--yes, -y` — skip confirmation

### Configuration keys

- `default_branch` (default: `main`)
- `default_commit_message`
- `default_license` (default: `MIT`)
- `default_project_type` (default: `python`)
- `auto_push` (default: `false`)
- `conventional_commits` (default: `false`)
- `editor`
- `git_user_name`, `git_user_email`
- `safe_mode` (default: `false`)
- `test_branch_prefix` (default: `test`)
- `auto_create_pr` (default: `true`)
- `pr_base_branch` (default: `main`)

### Per-repo overrides

A `.git-auto.json` at the repository root overrides the user config for that
project. Precedence: built-in defaults < user config < repo-local file.

## Utility

### `git-auto version`

Show the installed version.

## Environment Variables

- `GIT_AUTO_DEBUG=1` — enable debug logging to `~/.git-auto.log` (and stderr).

## Shell Completion

```bash
git-auto --install-completion    # install for your shell (bash/zsh/fish)
```

---
