"""Tests for GitHub Pull Request management (github_pr/pr_manager.py)."""

from unittest.mock import patch, MagicMock

import pytest

from git_auto_pro.github_pr.pr_manager import (
    create_pull_request,
    list_pull_requests,
    merge_pull_request,
    get_pull_request,
    review_pr_in_browser,
)


@pytest.fixture
def mock_session():
    with patch("git_auto_pro.github.get_authenticated_session") as mock:
        yield mock


@pytest.fixture
def mock_user():
    with patch("git_auto_pro.github.get_current_user") as mock:
        mock.return_value = {"login": "testuser"}
        yield mock


def test_create_pull_request(mock_session, mock_user):
    session = mock_session.return_value
    session.post.return_value.json.return_value = {
        "number": 5,
        "html_url": "https://github.com/testuser/repo/pull/5",
    }
    session.post.return_value.status_code = 201

    result = create_pull_request(head="feature", base="main", title="Add feature", repo="repo")

    assert result["number"] == 5
    session.post.assert_called_once()
    url = session.post.call_args[0][0]
    assert url.endswith("/repos/testuser/repo/pulls")
    body = session.post.call_args[1]["json"]
    assert body["title"] == "Add feature"
    assert body["head"] == "feature"
    assert body["base"] == "main"


def test_create_pull_request_owner_name_repo(mock_session, mock_user):
    """Passing repo='owner/name' uses that owner, not the authed user."""
    session = mock_session.return_value
    session.post.return_value.json.return_value = {"number": 1, "html_url": "u"}
    session.post.return_value.status_code = 201

    create_pull_request(head="h", base="main", title="t", repo="myorg/myrepo")

    url = session.post.call_args[0][0]
    assert url.endswith("/repos/myorg/myrepo/pulls")


def test_create_pull_request_with_reviewers_and_labels(mock_session, mock_user):
    session = mock_session.return_value
    session.post.return_value.json.return_value = {"number": 7, "html_url": "u"}
    session.post.return_value.status_code = 201

    create_pull_request(
        head="h", base="main", title="t",
        reviewers=["alice"], labels=["bug"], repo="repo",
    )

    # 1 PR-create POST + 1 reviewer POST + 1 label POST
    assert session.post.call_count == 3
    reviewer_url = session.post.call_args_list[1][0][0]
    assert "requested_reviewers" in reviewer_url
    label_url = session.post.call_args_list[2][0][0]
    assert "labels" in label_url


def test_list_pull_requests(mock_session, mock_user):
    session = mock_session.return_value
    session.get.return_value.json.return_value = [
        {"number": 1, "title": "PR 1", "head": {"ref": "f1"}, "user": {"login": "u"}},
        {"number": 2, "title": "PR 2", "head": {"ref": "f2"}, "user": {"login": "u"}},
    ]
    session.get.return_value.status_code = 200
    session.get.return_value.headers = {}

    results = list_pull_requests(repo="repo")

    assert len(results) == 2
    assert results[0]["number"] == 1
    session.get.assert_called_once()


def test_merge_pull_request(mock_session, mock_user):
    session = mock_session.return_value
    session.put.return_value.status_code = 200

    result = merge_pull_request(42, "squash", repo="repo")

    assert result is True
    url = session.put.call_args[0][0]
    assert url.endswith("/repos/testuser/repo/pulls/42/merge")
    assert session.put.call_args[1]["json"]["merge_method"] == "squash"


def test_merge_pull_request_dry_run(mock_session, mock_user):
    """--dry-run must not call the API."""
    session = mock_session.return_value

    result = merge_pull_request(42, "merge", repo="repo", dry_run=True)

    assert result is True
    session.put.assert_not_called()


def test_merge_pull_request_invalid_method(mock_session, mock_user):
    result = merge_pull_request(42, "bogus", repo="repo")
    assert result is False


def test_get_pull_request(mock_session, mock_user):
    session = mock_session.return_value
    session.get.return_value.json.return_value = {
        "number": 3, "title": "PR 3", "state": "open",
        "user": {"login": "u"}, "head": {"ref": "f"}, "base": {"ref": "main"},
        "created_at": "2026-01-01T00:00:00Z", "html_url": "u",
    }
    session.get.return_value.status_code = 200

    result = get_pull_request(3, repo="repo")

    assert result["number"] == 3
    assert session.get.call_args[0][0].endswith("/pulls/3")


def test_review_pr_in_browser(mock_session, mock_user):
    with patch("git_auto_pro.github_pr.pr_manager.webbrowser") as mock_wb:
        review_pr_in_browser(9, repo="owner/repo")
        mock_wb.open.assert_called_once()
        opened = mock_wb.open.call_args[0][0]
        assert opened == "https://github.com/owner/repo/pull/9"
