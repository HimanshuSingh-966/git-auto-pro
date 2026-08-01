# Contributing to Git-Auto Pro

Thanks for helping improve Git-Auto Pro. This guide covers how to set up the
development environment, the coding standards we follow, and how to submit
changes.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

Be respectful, collaborative, and constructive. Report unacceptable behavior to
the maintainers.

## Development Setup

Git-Auto Pro is a pure-Python CLI (Python 3.8+). The fastest way to get set up
is the `Makefile`:

```bash
git clone https://github.com/HimanshuSingh-966/git-auto-pro.git
cd git-auto-pro

# Create a virtualenv and install the package (editable) with dev dependencies
make install          # or: python -m venv venv && venv/bin/pip install -e ".[dev]"
source venv/bin/activate

# Verify it works
git-auto --help
```

The dev extra installs `pytest`, `pytest-cov`, `black`, `ruff`, and `mypy`.

### Useful Make targets

| Target | What it does |
|--------|--------------|
| `make install` | Create `venv/` and `pip install -e ".[dev]"` |
| `make test` | Run the test suite (`pytest`) |
| `make test-cov` | Tests + coverage report (`htmlcov/`) |
| `make lint` | `black --check` + `ruff check` |
| `make format` | `black` + `ruff check --fix` |
| `make typecheck` | `mypy git_auto_pro/` |
| `make check` | lint + typecheck + tests (pre-PR gate) |
| `make build` | Clean + build sdist/wheel into `dist/` |

## Running Tests

```bash
# Whole suite
pytest

# A single file / test
pytest tests/test_git_commands.py
pytest tests/test_cli.py::TestGitCommands::test_status_no_repo

# With coverage
pytest --cov=git_auto_pro --cov-report=term-missing
```

The suite is offline — GitHub API calls and `keyring` are mocked, so no token
or network is required. Tests use `tmp_path`/`temp_repo` fixtures and must
**not** write to your real `~/.git-auto-config.json` (see "Test isolation"
below).

### Writing tests

- One `tests/test_<module>.py` per source module.
- Use the existing fixtures in `tests/conftest.py`:
  - `temp_dir` — a throwaway directory
  - `temp_repo` — a real `git.Repo.init` with a configured test user
  - `_clear_github_auth_cache` (autouse) — resets the cached GitHub session/user between tests
- Mock GitHub at the `git_auto_pro.github.get_authenticated_session` /
  `get_current_user` boundary (see `tests/test_github_issues.py` for the pattern).
- **Test isolation:** when a test touches config, monkeypatch the file:

  ```python
  def test_example(tmp_path, monkeypatch):
      monkeypatch.setattr("git_auto_pro.config.CONFIG_FILE", tmp_path / "cfg.json")
      ...
  ```

  Never let a test write to the real home directory.

## Coding Standards

- **Style:** [Black](https://black.readthedocs.io/), line length 100 (configured in `pyproject.toml`). Lint with [Ruff](https://docs.astral.sh/ruff/). Run `make lint` before committing.
- **Types:** Type hints on public functions. `mypy git_auto_pro/` should be clean (`make typecheck`).
- **Python support:** Keep code compatible with Python 3.8+ (use `typing.Optional`/`typing.Dict` rather than the 3.9+ builtin generics in module-level annotations).
- **Imports:** Follow the existing style; the package uses `isort`-compatible ordering via the pre-commit config.
- **Errors:** Catch specific exceptions (`requests.ConnectionError`, `git.GitCommandError`, …) rather than bare `except:`.
- **Output:** Use the module-level `console = Console()` (Rich) for user-facing output; a `--json` flag exists for machine-readable output on list/view commands.

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`.
Keep the subject under 50 characters, imperative mood; wrap the body at 72.

Example:

```
feat(cli): add --json flag to issue list

Emit machine-readable JSON instead of a Rich table so the
output can be piped into jq and CI scripts.

Closes #123
```

## Pull Request Process

1. **Branch off `main`:** `git-auto switch -c feat/my-change` (or `fix/...`).
2. **Make your change**, add/update tests, and update docs (`README.md`,
   `docs/`, `CHANGELOG.md` as appropriate).
3. **Verify locally:** `make check` (lint + typecheck + tests) must pass.
4. **Commit** with a Conventional Commit message and push your branch.
5. **Open a PR** against `main` with a clear description, linked issues, and
   testing steps. One focused change per PR.
6. Address review feedback; a maintainer merges when approved.

After merge, delete your branch and sync `main`:

```bash
git-auto switch main
git-auto pull
```

## Reporting Bugs

Open an issue with: what you expected, what actually happened, minimal steps to
reproduce, and your environment (OS, Python version, `git-auto version`). You
can create it from the CLI:

```bash
git-auto issue create --title "[BUG] ..." --labels bug
```

## Suggesting Enhancements

Open an issue describing the problem you're solving, the proposed behavior, and
any alternatives considered. Check open issues first to avoid duplicates.

## License

By contributing, you agree your contributions are licensed under the project's
MIT License (see `LICENSE`).
