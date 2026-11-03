from __future__ import annotations

from datetime import date, timedelta

import pytest

from profile_cards.metrics import streaks, top_languages
from profile_cards.models import ContributionDay, Repo

TODAY = date(2026, 11, 3)


def _days(counts: list[int]) -> list[ContributionDay]:
    """counts[-1] is today, counts[-2] yesterday, and so on."""
    start = TODAY - timedelta(days=len(counts) - 1)
    return [ContributionDay(start + timedelta(days=i), c) for i, c in enumerate(counts)]


@pytest.mark.parametrize(
    ("counts", "current", "longest"),
    [
        ([], 0, 0),
        ([0, 0, 0], 0, 0),
        ([1, 1, 1], 3, 3),
        # An empty today keeps yesterday's streak alive.
        ([1, 1, 0], 2, 2),
        ([1, 0, 0], 0, 1),
        ([1, 1, 1, 1, 0, 1, 1], 2, 4),
    ],
)
def test_streaks(counts: list[int], current: int, longest: int) -> None:
    result = streaks(_days(counts), TODAY)
    assert (result.current, result.longest) == (current, longest)


def _repo(name: str, languages: dict[str, int]) -> Repo:
    return Repo(name, False, 0, None, None, {k: (v, None) for k, v in languages.items()})


def test_top_languages_excludes_and_buckets_other() -> None:
    repos = [
        _repo("a", {"Python": 600, "HTML": 1000, "Go": 100}),
        _repo("b", {"Python": 200, "TypeScript": 300, "Rust": 50}),
    ]
    shares = top_languages(repos, frozenset({"HTML"}), limit=2)
    assert [s.name for s in shares] == ["Python", "TypeScript", "Other"]
    assert shares[0].share == pytest.approx(800 / 1250)
    assert sum(s.share for s in shares) == pytest.approx(1)


def test_top_languages_empty() -> None:
    assert top_languages([], frozenset(), limit=5) == []
