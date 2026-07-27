"""Tests for backup/restore round-trip — history must survive."""

from pathlib import Path

import git

from git_auto_pro.backup import create_backup, restore_backup


def test_backup_preserves_commit_history(temp_repo, monkeypatch, tmp_path):
    """Regression: a backup must include .git/objects so a restored repo
    actually has its history. Previously only .git/{config,HEAD,refs,hooks}
    were archived, leaving refs pointing at missing objects.
    """
    monkeypatch.chdir(temp_repo.working_dir)

    # Create real history.
    f = Path(temp_repo.working_dir) / "hello.txt"
    f.write_text("hi")
    temp_repo.index.add(["hello.txt"])
    temp_repo.index.commit("first commit")
    commit_sha = str(temp_repo.head.commit.hexsha)

    backup_file = str(tmp_path / "backup.tar.gz")
    create_backup(backup_file)
    assert Path(backup_file).exists()

    # restore_backup extracts into ./restored relative to cwd.
    restore_backup(backup_file)
    restored = Path(temp_repo.working_dir) / "restored"

    # objects/ must be present — that's the whole point of the fix.
    assert (restored / ".git" / "objects").exists(), "backup omitted .git/objects"

    # The restored repo must be valid and point at the same commit.
    r = git.Repo(str(restored))
    assert str(r.head.commit.hexsha) == commit_sha
    r.close()
