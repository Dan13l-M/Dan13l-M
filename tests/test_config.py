from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import pytest

from profile_cards.config import Config, ConfigError, parse_config

ROOT = Path(__file__).resolve().parents[1]


def _raw() -> dict[str, Any]:
    with (ROOT / "config.toml").open("rb") as fh:
        return tomllib.load(fh)


def test_repo_config_loads(cfg: Config) -> None:
    assert cfg.identity.login == "Dan13l-M"
    assert cfg.identity.avatar is None
    assert cfg.crew
    assert {r.status for r in cfg.training.rounds} <= {"ring", "sparring", "next"}
    assert "HTML" in cfg.stats.exclude_languages


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d["identity"].pop("login"), "identity.login"),
        (lambda d: d["record"][0].update(stack=""), "record[0].stack"),
        (lambda d: d["training"]["rounds"][1].update(status="ko"), "training.rounds[1].status"),
        (lambda d: d["stats"].update(top_languages=True), "stats.top_languages"),
        (lambda d: d["identity"].update(avatar="missing.png"), "identity.avatar"),
    ],
)
def test_invalid_config_names_the_key(mutate: Any, message: str) -> None:
    data = _raw()
    mutate(data)
    with pytest.raises(ConfigError, match=message.replace("[", r"\[").replace("]", r"\]")):
        parse_config(data, ROOT)
