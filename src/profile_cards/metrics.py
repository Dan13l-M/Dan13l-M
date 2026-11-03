"""Derived numbers: streaks and language shares."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from profile_cards.models import ContributionDay, Repo

FALLBACK_LANGUAGE_COLOR = "#b537f2"


@dataclass(frozen=True)
class Streaks:
    current: int
    longest: int


def streaks(days: Iterable[ContributionDay], today: date) -> Streaks:
    active = {d.day for d in days if d.count > 0}
    if not active:
        return Streaks(0, 0)

    # Like GitHub: an empty "today" doesn't break the streak until the day is over.
    cursor = today if today in active else today - timedelta(days=1)
    current = 0
    while cursor in active:
        current += 1
        cursor -= timedelta(days=1)

    longest = run = 0
    previous: date | None = None
    for day in sorted(active):
        run = run + 1 if previous is not None and day - previous == timedelta(days=1) else 1
        longest = max(longest, run)
        previous = day
    return Streaks(current, longest)


@dataclass(frozen=True)
class LanguageShare:
    name: str
    share: float
    color: str


def top_languages(
    repos: Iterable[Repo], exclude: frozenset[str], limit: int
) -> list[LanguageShare]:
    totals: dict[str, int] = {}
    colors: dict[str, str] = {}
    for repo in repos:
        for name, (size, color) in repo.languages.items():
            if name in exclude:
                continue
            totals[name] = totals.get(name, 0) + size
            if color and name not in colors:
                colors[name] = color

    grand = sum(totals.values())
    if grand == 0:
        return []
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    shares = [
        LanguageShare(name, size / grand, colors.get(name, FALLBACK_LANGUAGE_COLOR))
        for name, size in ranked[:limit]
    ]
    rest = sum(size for _, size in ranked[limit:])
    if rest:
        shares.append(LanguageShare("Other", rest / grand, "#555570"))
    return shares
