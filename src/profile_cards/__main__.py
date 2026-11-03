"""CLI: render every panel into the output directory."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from profile_cards.config import ConfigError, load_config
from profile_cards.github import GitHubError, fetch_payload, parse_profile
from profile_cards.panels import Context, crew_markdown, inject_crew, render_all
from profile_cards.svg import font_css


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="profile-cards", description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.toml"))
    parser.add_argument("--out", type=Path, default=Path("generated"))
    parser.add_argument("--fonts", type=Path, default=Path("assets/fonts"))
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument(
        "--fixture", type=Path, help="GraphQL response JSON to use instead of calling the API"
    )
    parser.add_argument("--today", type=date.fromisoformat, help="override today (YYYY-MM-DD)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        cfg = load_config(args.config)
        if args.fixture:
            payload = json.loads(args.fixture.read_text(encoding="utf-8"))
        else:
            token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
            if not token:
                print("error: set GH_TOKEN or GITHUB_TOKEN, or pass --fixture", file=sys.stderr)
                return 2
            payload = fetch_payload(cfg.identity.login, token)
        profile = parse_profile(payload)
    except (ConfigError, GitHubError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    today = args.today or datetime.now(UTC).date()
    ctx = Context(cfg=cfg, profile=profile, fonts=font_css(args.fonts), today=today)
    files = render_all(ctx)

    args.out.mkdir(parents=True, exist_ok=True)
    # Crew cards are named after repos; drop cards for repos removed from the config.
    for stale in args.out.glob("crew-*.svg"):
        if stale.name not in files:
            stale.unlink()
    for name, content in files.items():
        (args.out / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"wrote {len(files)} panels to {args.out}")

    if args.readme.is_file():
        current = args.readme.read_text(encoding="utf-8")
        updated = inject_crew(current, crew_markdown(cfg, args.out.as_posix()))
        if updated != current:
            args.readme.write_text(updated, encoding="utf-8", newline="\n")
            print(f"updated crew links in {args.readme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
