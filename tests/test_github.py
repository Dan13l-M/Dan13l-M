from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from profile_cards.github import GitHubError, parse_profile
from profile_cards.models import Profile


def test_parse_profile(profile: Profile) -> None:
    assert profile.login == "Dan13l-M"
    assert profile.total_contributions == 48
    assert profile.commits == 40
    assert len(profile.days) == 17
    assert profile.days[0].day == date(2026, 10, 18)

    mochi = profile.repo("MOCHI-API")
    assert mochi is not None
    assert mochi.is_private
    assert mochi.languages["Python"] == (12000, "#3572A5")


def test_repo_without_language(profile: Profile) -> None:
    showcase = profile.repo("todo-fit-plus-showcase")
    assert showcase is not None
    assert showcase.primary_language is None
    assert showcase.languages == {}


def _viewer(login: str) -> dict[str, Any]:
    node = {
        "name": "secret-lab",
        "isPrivate": True,
        "stargazerCount": 0,
        "primaryLanguage": {"name": "Python", "color": "#3572A5"},
        "languages": {"edges": [{"size": 500, "node": {"name": "Python", "color": "#3572A5"}}]},
    }
    return {"data": {"viewer": {"login": login, "repositories": {"nodes": [node]}}}}


def test_viewer_repos_replace_user_repos_for_the_owner(payload: dict[str, Any]) -> None:
    profile = parse_profile(payload, _viewer("dan13l-m"))
    assert [r.name for r in profile.repos] == ["secret-lab"]
    assert profile.repos[0].is_private


@pytest.mark.parametrize("viewer", [None, {"errors": [{"message": "nope"}]}, {"data": {}}])
def test_missing_viewer_keeps_user_repos(payload: dict[str, Any], viewer: Any) -> None:
    assert parse_profile(payload, viewer).repo("UrbanFlow") is not None


def test_someone_elses_viewer_is_ignored(payload: dict[str, Any]) -> None:
    profile = parse_profile(payload, _viewer("github-actions[bot]"))
    assert profile.repo("secret-lab") is None


@pytest.mark.parametrize(
    "bad",
    [
        {"errors": [{"message": "Bad credentials"}]},
        {"data": {"user": None}},
        {},
    ],
)
def test_parse_profile_rejects_bad_payloads(bad: dict[str, Any]) -> None:
    with pytest.raises(GitHubError):
        parse_profile(bad)
