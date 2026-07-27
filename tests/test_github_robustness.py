"""Tests for Tier 2 robustness helpers: URL encoding, pagination,
rate-limit detection, and auth-cache invalidation."""

from unittest.mock import patch, MagicMock

import requests

from git_auto_pro.github import (
    _api_url,
    _next_link,
    _paginated_get,
    _is_rate_limited,
    clear_auth_cache,
    get_authenticated_session,
    get_current_user,
    GITHUB_API_URL,
)


class TestApiUrl:
    def test_plain_segments(self):
        assert _api_url("repos", "owner", "repo", "issues") == (
            f"{GITHUB_API_URL}/repos/owner/repo/issues"
        )

    def test_encodes_special_characters(self):
        # A branch name with '#' / '?' would otherwise break or inject.
        url = _api_url("repos", "owner", "repo", "branches", "feat?#x", "protection")
        assert url == (
            f"{GITHUB_API_URL}/repos/owner/repo/branches/feat%3F%23x/protection"
        )

    def test_encodes_spaces(self):
        url = _api_url("repos", "owner", "my repo", "issues")
        assert url == f"{GITHUB_API_URL}/repos/owner/my%20repo/issues"

    def test_slashes_within_a_segment_are_encoded(self):
        # A segment must not be able to escape its position with a literal '/'.
        url = _api_url("repos", "owner", "ev/il", "issues")
        assert url == f"{GITHUB_API_URL}/repos/owner/ev%2Fil/issues"

    def test_int_segment_is_accepted(self):
        assert _api_url("repos", "owner", "repo", "issues", 42) == (
            f"{GITHUB_API_URL}/repos/owner/repo/issues/42"
        )


class TestNextLink:
    def test_extracts_next_url(self):
        link = '<https://api.github.com/x?page=2>; rel="next", <...>; rel="last"'
        assert _next_link(link) == "https://api.github.com/x?page=2"

    def test_no_next_returns_none(self):
        assert _next_link('<https://api.github.com/x?page=5>; rel="last"') is None

    def test_empty_returns_none(self):
        assert _next_link("") is None

    def test_non_string_returns_none(self):
        # Defensive: mocked responses hand back non-string header values.
        assert _next_link(None) is None  # type: ignore[arg-type]
        assert _next_link(MagicMock()) is None  # type: ignore[arg-type]


class TestIsRateLimited:
    def _resp(self, status, headers=None):
        r = MagicMock(spec=requests.Response)
        r.status_code = status
        r.headers = headers or {}
        return r

    def test_429_is_rate_limited(self):
        assert _is_rate_limited(self._resp(429)) is True

    def test_403_with_zero_remaining(self):
        assert _is_rate_limited(self._resp(403, {"X-RateLimit-Remaining": "0"})) is True

    def test_403_with_remaining_is_not_rate_limit(self):
        # A permissions 403, not a rate-limit 403.
        assert _is_rate_limited(self._resp(403, {"X-RateLimit-Remaining": "2500"})) is False

    def test_403_without_remaining_header(self):
        assert _is_rate_limited(self._resp(403, {})) is False

    def test_404_is_not_rate_limited(self):
        assert _is_rate_limited(self._resp(404, {"X-RateLimit-Remaining": "0"})) is False


class TestPaginatedGet:
    def _mock_session(self, pages):
        """pages: list of (json_list, link_header_or_None)."""
        responses = []
        for batch, link in pages:
            r = MagicMock()
            r.json.return_value = batch
            r.headers = {"Link": link} if link else {}
            r.raise_for_status.return_value = None
            responses.append(r)
        session = MagicMock()
        session.get.side_effect = responses
        return session

    def test_follows_next_until_limit(self):
        link1 = '<https://api.github.com/repos/o/r/issues?page=2>; rel="next"'
        session = self._mock_session([
            ([{"number": 1}, {"number": 2}], link1),
            ([{"number": 3}, {"number": 4}], None),
        ])
        result = _paginated_get(session, "https://api.github.com/repos/o/r/issues", {"state": "open"}, 10, "List issues")
        assert [i["number"] for i in result] == [1, 2, 3, 4]
        assert session.get.call_count == 2
        # First call uses params; second uses the next URL verbatim (no params).
        first_args = session.get.call_args_list[0]
        assert first_args.args[0] == "https://api.github.com/repos/o/r/issues"
        # per_page = min(limit, 100) = 10 here.
        assert first_args.kwargs["params"]["per_page"] == 10
        second_args = session.get.call_args_list[1]
        assert second_args.args[0] == "https://api.github.com/repos/o/r/issues?page=2"
        assert second_args.kwargs["params"] is None

    def test_stops_at_limit(self):
        link1 = '<https://api.github.com/x?page=2>; rel="next"'
        session = self._mock_session([
            ([{"number": 1}, {"number": 2}], link1),
        ])
        result = _paginated_get(session, "https://api.github.com/x", None, 2, "List")
        assert [i["number"] for i in result] == [1, 2]
        assert session.get.call_count == 1  # limit reached, no second fetch

    def test_single_page_no_next(self):
        session = self._mock_session([([{"number": 1}], None)])
        result = _paginated_get(session, "https://api.github.com/x", None, 30, "List")
        assert result == [{"number": 1}]
        assert session.get.call_count == 1

    def test_empty_result(self):
        session = self._mock_session([([], None)])
        assert _paginated_get(session, "https://api.github.com/x", None, 30, "List") == []


class TestAuthCache:
    @patch("git_auto_pro.github.get_stored_token", return_value="tok")
    def test_session_is_cached(self, _mock_token):
        s1 = get_authenticated_session()
        s2 = get_authenticated_session()
        assert s1 is s2

    @patch("git_auto_pro.github.get_stored_token", return_value="tok")
    def test_clear_auth_cache_rebuilds_session(self, _mock_token):
        s1 = get_authenticated_session()
        clear_auth_cache()
        s2 = get_authenticated_session()
        # Real Session objects (requests.Session isn't mocked), so after
        # clearing the cache a fresh one is built.
        assert s1 is not s2

    @patch("git_auto_pro.github.get_authenticated_session")
    def test_current_user_is_cached(self, mock_session):
        # get_current_user uses session.get(...), not the module-level requests.get.
        mock_session.return_value.get.return_value.json.return_value = {"login": "me"}
        mock_session.return_value.get.return_value.raise_for_status.return_value = None
        u1 = get_current_user()
        u2 = get_current_user()
        assert u1 is u2
        assert mock_session.return_value.get.call_count == 1  # one /user round-trip
