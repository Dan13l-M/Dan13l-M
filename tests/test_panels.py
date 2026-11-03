from __future__ import annotations

import dataclasses
import re
import xml.etree.ElementTree as ET

import pytest

from profile_cards.config import Config, CrewItem
from profile_cards.panels import (
    CREW_END,
    CREW_START,
    Context,
    crew_card,
    crew_markdown,
    inject_crew,
    render_all,
)
from profile_cards.svg import wrap


def test_every_panel_is_valid_svg(ctx: Context) -> None:
    files = render_all(ctx)
    assert "hero.svg" in files
    assert any(name.startswith("crew-") for name in files)
    for name, content in files.items():
        root = ET.fromstring(content)
        assert root.tag == "{http://www.w3.org/2000/svg}svg", name


def test_panels_have_no_external_resources(ctx: Context) -> None:
    # GitHub's image proxy blocks external fetches from SVGs, so anything external breaks.
    for name, content in render_all(ctx).items():
        assert not re.search(r'href="https?:', content), name
        assert not re.search(r"url\(https?:", content), name


def test_user_text_is_escaped(ctx: Context) -> None:
    item = CrewItem(repo="x", title="<Tag> & co", mission='Says "hi" <script>', tags=("a&b",))
    content = crew_card(ctx, 0, item)
    ET.fromstring(content)
    assert "&lt;script&gt;" in content
    assert "<script>" not in content


def test_live_numbers_reach_the_panels(ctx: Context) -> None:
    files = render_all(ctx)
    assert ">48<" in files["power.svg"]
    # 12 of the fixture's 17 calendar days have activity; it owns 3 repos.
    assert ">12<" in files["power.svg"]
    assert ">3<" in files["power.svg"]
    assert "48" in files["wanted.svg"]
    assert "★ 2" in files["crew-urbanflow.svg"]


def test_panels_render_with_no_activity(ctx: Context) -> None:
    empty = dataclasses.replace(ctx.profile, days=(), repos=(), total_contributions=0)
    files = render_all(dataclasses.replace(ctx, profile=empty))
    assert "no contributions recorded yet" in files["voyage.svg"]
    assert "no language data yet" in files["power.svg"]


def test_inject_crew_replaces_only_the_block(cfg: Config) -> None:
    readme = f"top\n{CREW_START}\nold\n{CREW_END}\nbottom\n"
    block = crew_markdown(cfg, "generated")
    once = inject_crew(readme, block)
    assert once.startswith("top\n") and once.endswith("\nbottom\n")
    assert "old" not in once
    assert "generated/crew-urbanflow.svg" in once
    assert inject_crew(once, block) == once


def test_inject_crew_without_markers_is_a_no_op(cfg: Config) -> None:
    assert inject_crew("plain readme", crew_markdown(cfg, "generated")) == "plain readme"


@pytest.mark.parametrize(
    ("value", "width", "max_lines", "expected"),
    [
        ("short", 10, None, ["short"]),
        ("", 10, None, [""]),
        ("one two three four", 9, 1, ["one two…"]),
    ],
)
def test_wrap(value: str, width: int, max_lines: int | None, expected: list[str]) -> None:
    assert wrap(value, width, max_lines) == expected
