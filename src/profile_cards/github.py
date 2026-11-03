"""Fetch profile data from the GitHub GraphQL API and parse it into models."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import date
from typing import Any

from profile_cards.models import ContributionDay, Profile, Repo

API_URL = "https://api.github.com/graphql"

QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name
        isPrivate
        stargazerCount
        primaryLanguage { name color }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


class GitHubError(RuntimeError):
    pass


def fetch_payload(login: str, token: str, timeout: float = 30.0) -> dict[str, Any]:
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-cards",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload: dict[str, Any] = json.load(response)
    except urllib.error.HTTPError as exc:
        # Never echo the request: it carries the token.
        raise GitHubError(f"GitHub API returned HTTP {exc.code}") from None
    except urllib.error.URLError as exc:
        raise GitHubError(f"GitHub API unreachable: {exc.reason}") from None
    return payload


def parse_profile(payload: dict[str, Any]) -> Profile:
    if payload.get("errors"):
        messages = "; ".join(str(e.get("message", e)) for e in payload["errors"])
        raise GitHubError(f"GraphQL errors: {messages}")
    user = (payload.get("data") or {}).get("user")
    if not user:
        raise GitHubError("GraphQL response has no user (wrong login?)")

    cc = user["contributionsCollection"]
    calendar = cc["contributionCalendar"]
    days = tuple(
        ContributionDay(day=date.fromisoformat(d["date"]), count=int(d["contributionCount"]))
        for week in calendar["weeks"]
        for d in week["contributionDays"]
    )

    repos: list[Repo] = []
    for node in user["repositories"]["nodes"]:
        primary = node.get("primaryLanguage") or {}
        languages = {
            edge["node"]["name"]: (int(edge["size"]), edge["node"].get("color"))
            for edge in (node.get("languages") or {}).get("edges", [])
        }
        repos.append(
            Repo(
                name=node["name"],
                is_private=bool(node["isPrivate"]),
                stars=int(node["stargazerCount"]),
                primary_language=primary.get("name"),
                primary_color=primary.get("color"),
                languages=languages,
            )
        )

    return Profile(
        login=user["login"],
        followers=int(user["followers"]["totalCount"]),
        total_contributions=int(calendar["totalContributions"]),
        commits=int(cc["totalCommitContributions"]),
        pull_requests=int(cc["totalPullRequestContributions"]),
        reviews=int(cc["totalPullRequestReviewContributions"]),
        issues=int(cc["totalIssueContributions"]),
        days=days,
        repos=tuple(repos),
    )
