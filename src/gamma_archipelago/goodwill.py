"""Versioned shared goodwill: hostile factions keep their dedicated reward gates."""

from __future__ import annotations

import json
from collections.abc import Callable
from importlib.resources import files
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .configuration import SeedConfiguration
SHARED_ID = 28051309
SHARED_NAME = "Faction Goodwill: All Factions"
ALLIED_ID = 28051310
ALLIED_NAME = "Faction Goodwill: Allied Factions"
_catalog = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
FRIENDLY = (
    frozenset(_catalog["faction_standing_factions"])
    - _catalog["settlement_relations"]["factions"].keys()
)


def shared(configuration: SeedConfiguration) -> bool:
    return bool(
        configuration.option("shared_faction_goodwill")
        and "rewards_faction_reputation" in configuration.rewards
    )


def shared_name(configuration: SeedConfiguration) -> str:
    return ALLIED_NAME if configuration.option("shared_faction_goodwill") == 2 else SHARED_NAME


def selected_id(configuration: SeedConfiguration) -> int | None:
    if not shared(configuration):
        return None
    return ALLIED_ID if configuration.option("shared_faction_goodwill") == 2 else SHARED_ID


def copies(configuration: SeedConfiguration, name: str, count: Callable[[str], int]) -> int:
    common = count(shared_name(configuration)) if shared(configuration) else 0
    if name in {SHARED_NAME, ALLIED_NAME}:
        return common if name == shared_name(configuration) else 0
    if (
        configuration.option("shared_faction_goodwill") == 2
        and name.removeprefix("Faction Goodwill: ") not in FRIENDLY
    ):
        return count(name)
    return count(name) + common


def pool_name(configuration: SeedConfiguration, name: str) -> str:
    if shared(configuration) and (
        configuration.option("shared_faction_goodwill") == 1
        or name.removeprefix("Faction Goodwill: ") in FRIENDLY
    ):
        return shared_name(configuration)
    return name
