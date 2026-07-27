"""Tests for GitHub remote URL parsing and repo-owner resolution."""

from unittest.mock import patch

from git_auto_pro.github import parse_remote_url, resolve_repo_ref


class TestParseRemoteUrl:
    def test_https_with_dot_git(self):
        assert parse_remote_url("https://github.com/owner/repo.git") == ("owner", "repo")

    def test_https_without_dot_git(self):
        assert parse_remote_url("https://github.com/owner/repo") == ("owner", "repo")

    def test_https_trailing_slash(self):
        assert parse_remote_url("https://github.com/owner/repo/") == ("owner", "repo")

    def test_scp_like_ssh(self):
        assert parse_remote_url("git@github.com:owner/repo.git") == ("owner", "repo")

    def test_ssh_scheme(self):
        assert parse_remote_url("ssh://git@github.com/owner/repo.git") == ("owner", "repo")

    def test_git_scheme(self):
        assert parse_remote_url("git://github.com/owner/repo.git") == ("owner", "repo")

    def test_org_and_dotted_repo_name(self):
        assert parse_remote_url("https://github.com/my-org/my.repo.git") == ("my-org", "my.repo")

    def test_unparseable_has_no_owner(self):
        owner, _ = parse_remote_url("not a url")
        assert owner is None

    def test_empty_returns_none(self):
        assert parse_remote_url("") == (None, None)


class TestResolveRepoRef:
    def test_owner_name_form(self):
        assert resolve_repo_ref("owner/repo") == ("owner", "repo")

    def test_owner_name_strips_whitespace(self):
        assert resolve_repo_ref("  owner / repo  ") == ("owner", "repo")

    @patch("git_auto_pro.github.get_current_user")
    def test_bare_name_uses_authenticated_user(self, mock_user):
        mock_user.return_value = {"login": "me"}
        assert resolve_repo_ref("myrepo") == ("me", "myrepo")

    @patch("git_auto_pro.github.detect_repo_from_remote")
    def test_none_detects_from_remote(self, mock_detect):
        mock_detect.return_value = ("detected-owner", "detected-repo")
        assert resolve_repo_ref(None) == ("detected-owner", "detected-repo")
