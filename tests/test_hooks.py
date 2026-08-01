"""Tests for generated git hooks — POSIX sh portability."""

import shutil
import subprocess

import pytest

from git_auto_pro.scaffolding.hooks import (
    PRE_COMMIT_HOOK,
    PRE_PUSH_HOOK,
    COMMIT_MSG_HOOK,
    POST_COMMIT_HOOK,
)


def test_pre_commit_hook_is_posix_sh_safe():
    assert PRE_COMMIT_HOOK.startswith("#!/bin/sh")
    assert "&>" not in PRE_COMMIT_HOOK, "bash-only &> redirect breaks /bin/sh (dash)"
    assert "> /dev/null 2>&1" in PRE_COMMIT_HOOK


def test_pre_push_hook_is_posix_sh_safe():
    assert PRE_PUSH_HOOK.startswith("#!/bin/sh")
    assert "&>" not in PRE_PUSH_HOOK, "bash-only &> redirect breaks /bin/sh (dash)"
    assert "> /dev/null 2>&1" in PRE_PUSH_HOOK


def test_all_four_hooks_present():
    # Regression for the accidental duplicate-module deletion: the four hook
    # constants must still exist and the github_templates duplicate must not.
    assert PRE_COMMIT_HOOK and PRE_PUSH_HOOK and COMMIT_MSG_HOOK and POST_COMMIT_HOOK


@pytest.mark.skipif(shutil.which("dash") is None, reason="dash not installed")
def test_pre_commit_hook_skips_cleanly_under_dash_with_no_tools(tmp_path):
    """Regression: under dash, with lint/test tools absent, the pre-commit
    hook must skip (exit 0), not fail. Previously `&> /dev/null` was parsed
    by dash as `&` (background) + `> /dev/null`, making the `command -v`
    guard always pass and running the (missing) tool, which failed the hook.
    """
    hook = tmp_path / "pre-commit"
    hook.write_text(PRE_COMMIT_HOOK)
    hook.chmod(0o755)

    # Invoke dash by absolute path (so it starts even with an empty PATH),
    # but give the hook an empty PATH so `command -v ruff/black/pytest` all
    # fail to find their tools and the guards skip.
    result = subprocess.run(
        [shutil.which("dash"), str(hook)],
        capture_output=True,
        env={"PATH": "/nonexistent"},
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")


@pytest.mark.skipif(shutil.which("dash") is None, reason="dash not installed")
def test_pre_push_hook_skips_cleanly_under_dash_with_no_tools(tmp_path):
    hook = tmp_path / "pre-push"
    hook.write_text(PRE_PUSH_HOOK)
    hook.chmod(0o755)

    result = subprocess.run(
        [shutil.which("dash"), str(hook)],
        capture_output=True,
        env={"PATH": "/nonexistent"},
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
