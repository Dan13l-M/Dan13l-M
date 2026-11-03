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
