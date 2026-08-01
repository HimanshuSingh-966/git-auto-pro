"""Tier 3 tests: per-repo config, --json output, --dry-run no-ops,
git-auto sync, and doctor token-scope checks."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from git_auto_pro.cli import app
from git_auto_pro.config import load_config

runner = CliRunner()


# ───────────────────────── per-repo config ─────────────────────────

def test_repo_config_overrides_user(temp_repo, monkeypatch, tmp_path):
    """A repo-local .git-auto.json must win over the user config."""
    user_cfg = tmp_path / "user.json"
    user_cfg.write_text(json.dumps({"default_branch": "main"}))
    monkeypatch.setattr("git_auto_pro.config.CONFIG_FILE", user_cfg)

    (Path(temp_repo.working_dir) / ".git-auto.json").write_text(
        json.dumps({"default_branch": "develop"})
    )
    monkeypatch.chdir(temp_repo.working_dir)

    assert load_config()["default_branch"] == "develop"


def test_user_config_used_without_repo_file(temp_repo, monkeypatch, tmp_path):
    """Without a .git-auto.json, the user config value is used."""
    user_cfg = tmp_path / "user.json"
    user_cfg.write_text(json.dumps({"default_branch": "main"}))
    monkeypatch.setattr("git_auto_pro.config.CONFIG_FILE", user_cfg)
    monkeypatch.chdir(temp_repo.working_dir)

    assert load_config()["default_branch"] == "main"


# ───────────────────────── --json output ─────────────────────────

def test_stats_json(temp_repo, monkeypatch):
    """`git-auto stats --json` emits valid JSON with the repo stats."""
    monkeypatch.chdir(temp_repo.working_dir)
    (Path(temp_repo.working_dir) / "a.txt").write_text("a")
    temp_repo.index.add(["a.txt"])
    temp_repo.index.commit("first")

    result = runner.invoke(app, ["stats", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["total_commits"] == 1
    assert "current_branch" in data
    assert isinstance(data["top_contributors"], list)


# ───────────────────────── --dry-run no-ops ─────────────────────────

def test_undo_dry_run_does_not_change_history(temp_repo, monkeypatch):
    """`git-auto undo --dry-run` must not actually reset."""
    monkeypatch.chdir(temp_repo.working_dir)
    (Path(temp_repo.working_dir) / "a.txt").write_text("a")
    temp_repo.index.add(["a.txt"])
    temp_repo.index.commit("first")

    before = len(list(temp_repo.iter_commits()))
    result = runner.invoke(app, ["undo", "--dry-run"])
    after = len(list(temp_repo.iter_commits()))

    assert before == after
    assert "DRY RUN" in result.output


def test_release_dry_run_does_not_bump_files(temp_repo, monkeypatch):
    """`git-auto release patch --dry-run` must not modify version files."""
    monkeypatch.chdir(temp_repo.working_dir)
    pyproject = Path(temp_repo.working_dir) / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test-x"\nversion = "1.2.3"\n')
    before = pyproject.read_text()

    result = runner.invoke(app, ["release", "patch", "--dry-run"])

    assert pyproject.read_text() == before
    assert "DRY RUN" in result.output
    assert "1.2.4" in result.output  # shows the planned bump


def test_git_sync_dry_run_does_not_pull_or_push(monkeypatch):
    """git_sync(dry_run=True) must not call pull/push."""
    from git_auto_pro.git_commands import git_sync

    mock_repo = MagicMock()
    mock_repo.active_branch = "main"
    mock_remotes = MagicMock()
    mock_remotes.__bool__ = lambda self: True
    mock_repo.remotes = mock_remotes

    with patch("git_auto_pro.git_commands.get_repo", return_value=mock_repo):
        git_sync(dry_run=True)

    mock_repo.git.pull.assert_not_called()
    mock_repo.git.push.assert_not_called()


# ───────────────────────── doctor token scopes ─────────────────────────

def _doctor_run(monkeypatch, scopes_header):
    """Run diagnostics with a mocked token validation response."""
    from git_auto_pro.commands.doctor import run_diagnostics

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"login": "u"}
    mock_resp.headers = {"X-OAuth-Scopes": scopes_header}

    with patch("git_auto_pro.github.get_stored_token", return_value="tok"), \
         patch("git_auto_pro.github.check_api_connectivity", return_value=True), \
         patch("git_auto_pro.commands.doctor.requests") as mock_req, \
         patch("git_auto_pro.commands.doctor.git") as mock_git, \
         patch("git_auto_pro.commands.doctor.shutil") as mock_shutil, \
         patch("git_auto_pro.commands.doctor.load_config",
               return_value={"default_branch": "main", "safe_mode": False}):
        mock_req.get.return_value = mock_resp
        mock_shutil.which.return_value = "/usr/bin/git"
        mock_git.Repo.side_effect = Exception("not a repo")
        mock_git.InvalidGitRepositoryError = Exception
        return run_diagnostics(json_output=True)


def test_doctor_scopes_ok():
    """A token with repo+workflow scopes reports ok."""
    results = _doctor_run(None, "repo, workflow")
    token_row = [r for r in results if r["check"] == "GitHub token"][0]
    assert token_row["status"] == "ok"


def test_doctor_scopes_missing_workflow_warns():
    """A token missing the workflow scope warns."""
    results = _doctor_run(None, "repo")
    token_row = [r for r in results if r["check"] == "GitHub token"][0]
    assert token_row["status"] == "warn"
    assert "workflow" in token_row["fix"]
