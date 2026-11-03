from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from profile_cards.config import Config, load_config
from profile_cards.github import parse_profile
from profile_cards.models import Profile
from profile_cards.panels import Context
from profile_cards.svg import font_css

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def payload() -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / "graphql_user.json").read_text("utf-8"))
    return data


@pytest.fixture
def profile(payload: dict[str, Any]) -> Profile:
    return parse_profile(payload)


@pytest.fixture
def cfg() -> Config:
    return load_config(ROOT / "config.toml")


@pytest.fixture(scope="session")
def fonts() -> str:
    return font_css(ROOT / "assets" / "fonts")


@pytest.fixture
def ctx(cfg: Config, profile: Profile, fonts: str) -> Context:
    return Context(cfg=cfg, profile=profile, fonts=fonts, today=date(2026, 11, 3))
