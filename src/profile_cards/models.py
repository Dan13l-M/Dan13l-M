"""Plain data parsed from the GitHub API."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class ContributionDay:
    day: date
    count: int


@dataclass(frozen=True)
class Repo:
    name: str
    is_private: bool
    stars: int
    primary_language: str | None
    primary_color: str | None
    # Language name -> (bytes, color)
    languages: dict[str, tuple[int, str | None]] = field(default_factory=dict)


@dataclass(frozen=True)
class Profile:
    login: str
    followers: int
    total_contributions: int
    commits: int
    pull_requests: int
    reviews: int
    issues: int
    days: tuple[ContributionDay, ...]
    repos: tuple[Repo, ...]

    def repo(self, name: str) -> Repo | None:
        lowered = name.lower()
        return next((r for r in self.repos if r.name.lower() == lowered), None)
