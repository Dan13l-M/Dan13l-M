"""Load and validate config.toml into typed, immutable objects."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Status = Literal["ring", "sparring", "next"]
_STATUSES: tuple[Status, ...] = ("ring", "sparring", "next")


class ConfigError(ValueError):
    """Raised with the exact key path so a broken config is quick to fix."""


@dataclass(frozen=True)
class Identity:
    login: str
    name: str
    handle: str
    role: str
    location: str
    chips: tuple[str, ...]
    monogram: str
    avatar: Path | None


@dataclass(frozen=True)
class About:
    who: str
    now: tuple[str, ...]


@dataclass(frozen=True)
class RecordItem:
    attribute: str
    stack: str
    evidence: str


@dataclass(frozen=True)
class ArsenalGroup:
    label: str
    items: tuple[str, ...]


@dataclass(frozen=True)
class CrewItem:
    repo: str
    title: str
    mission: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class ClassifiedItem:
    title: str
    mission: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Round:
    title: str
    status: Status


@dataclass(frozen=True)
class Training:
    quote: str
    rounds: tuple[Round, ...]


@dataclass(frozen=True)
class StatsConfig:
    exclude_languages: frozenset[str]
    top_languages: int


@dataclass(frozen=True)
class Config:
    identity: Identity
    about: About
    record: tuple[RecordItem, ...]
    arsenal: tuple[ArsenalGroup, ...]
    crew: tuple[CrewItem, ...]
    classified: tuple[ClassifiedItem, ...]
    training: Training
    stats: StatsConfig


def _table(data: dict[str, Any], key: str, where: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"{where}{key}: expected a table")
    return value


def _tables(data: dict[str, Any], key: str, where: str) -> list[dict[str, Any]]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, dict) for v in value):
        raise ConfigError(f"{where}{key}: expected an array of tables")
    return value


def _str(data: dict[str, Any], key: str, where: str, *, allow_empty: bool = False) -> str:
    value = data.get(key)
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ConfigError(f"{where}{key}: expected a non-empty string")
    return value


def _strs(data: dict[str, Any], key: str, where: str) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ConfigError(f"{where}{key}: expected a list of strings")
    return tuple(value)


def _int(data: dict[str, Any], key: str, where: str, default: int) -> int:
    value = data.get(key, default)
    # bool is an int subclass; reject it so `top_languages = true` is an error.
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ConfigError(f"{where}{key}: expected a positive integer")
    return value


def parse_config(data: dict[str, Any], base_dir: Path) -> Config:
    ident = _table(data, "identity", "")
    avatar_raw = _str(ident, "avatar", "identity.", allow_empty=True) if "avatar" in ident else ""
    avatar = (base_dir / avatar_raw) if avatar_raw.strip() else None
    if avatar is not None and not avatar.is_file():
        raise ConfigError(f"identity.avatar: file not found: {avatar}")

    identity = Identity(
        login=_str(ident, "login", "identity."),
        name=_str(ident, "name", "identity."),
        handle=_str(ident, "handle", "identity."),
        role=_str(ident, "role", "identity."),
        location=_str(ident, "location", "identity."),
        chips=_strs(ident, "chips", "identity."),
        monogram=_str(ident, "monogram", "identity."),
        avatar=avatar,
    )

    about_t = _table(data, "about", "")
    about = About(who=_str(about_t, "who", "about."), now=_strs(about_t, "now", "about."))

    record = tuple(
        RecordItem(
            attribute=_str(t, "attribute", f"record[{i}]."),
            stack=_str(t, "stack", f"record[{i}]."),
            evidence=_str(t, "evidence", f"record[{i}]."),
        )
        for i, t in enumerate(_tables(data, "record", ""))
    )
    arsenal = tuple(
        ArsenalGroup(
            label=_str(t, "label", f"arsenal[{i}]."), items=_strs(t, "items", f"arsenal[{i}].")
        )
        for i, t in enumerate(_tables(data, "arsenal", ""))
    )
    crew = tuple(
        CrewItem(
            repo=_str(t, "repo", f"crew[{i}]."),
            title=_str(t, "title", f"crew[{i}]."),
            mission=_str(t, "mission", f"crew[{i}]."),
            tags=_strs(t, "tags", f"crew[{i}]."),
        )
        for i, t in enumerate(_tables(data, "crew", ""))
    )
    classified = tuple(
        ClassifiedItem(
            title=_str(t, "title", f"classified[{i}]."),
            mission=_str(t, "mission", f"classified[{i}]."),
            tags=_strs(t, "tags", f"classified[{i}]."),
        )
        for i, t in enumerate(_tables(data, "classified", ""))
    )

    training_t = _table(data, "training", "")
    rounds: list[Round] = []
    for i, t in enumerate(_tables(training_t, "rounds", "training.")):
        status = _str(t, "status", f"training.rounds[{i}].")
        if status not in _STATUSES:
            raise ConfigError(
                f"training.rounds[{i}].status: expected one of {', '.join(_STATUSES)}"
            )
        rounds.append(Round(title=_str(t, "title", f"training.rounds[{i}]."), status=status))
    training = Training(quote=_str(training_t, "quote", "training."), rounds=tuple(rounds))

    stats_t = data.get("stats", {})
    if not isinstance(stats_t, dict):
        raise ConfigError("stats: expected a table")
    stats = StatsConfig(
        exclude_languages=frozenset(_strs(stats_t, "exclude_languages", "stats.")),
        top_languages=_int(stats_t, "top_languages", "stats.", 5),
    )

    return Config(identity, about, record, arsenal, crew, classified, training, stats)


def load_config(path: Path) -> Config:
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    return parse_config(data, path.parent)
