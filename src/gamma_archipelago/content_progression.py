"""Shared content contracts for tool tiers, melter access and legacy manifests."""

import json
from collections.abc import Callable, Mapping
from importlib.resources import files
from typing import TYPE_CHECKING, Any

from .catalog import enabled_item_ids
from .tool_permissions import TOOL_ITEM_IDS, enabled
from .tool_permissions import level as permission_level

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

_data = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
TOOL_STASHES = tuple(
    row["name"]
    for row in sorted(_data["items"], key=lambda row: row.get("tool_level", 0))
    if "tool_level" in row
)
TOOL_CLAIMS = tuple("Claimed " + name.split(": ", 1)[1] for name in TOOL_STASHES)
TOOL_IDS = frozenset(row["id"] for row in _data["items"] if "tool_level" in row)


def tool_level(count: Callable[[str], int]) -> int:
    old, level = min(3, count("Progressive Tools")), 0
    for tier, name in enumerate(TOOL_CLAIMS, 1):
        if old < tier and not count(name):
            break
        level = tier
    return max(level, permission_level(count))


def configured_item_ids(configuration: "SeedConfiguration") -> frozenset[int]:
    ids = enabled_item_ids(configuration.rewards, configuration.gear)
    if enabled(configuration):
        return ids - TOOL_IDS - {28051802, 28051801}
    ids -= TOOL_ITEM_IDS
    return ids if configuration.option("content_progression") else ids - TOOL_IDS


def melter_check(configuration: "SeedConfiguration", row: Mapping[str, Any]) -> bool:
    return bool(
        configuration.option("content_progression")
        and row.get("quota_group") == "artefact"
        and row["minimum"] > 20
    )


def protected(configuration: "SeedConfiguration") -> frozenset[int]:
    if "rewards_artefact_melter" in configuration.rewards:
        return frozenset()
    return frozenset(row["id"] for row in _data["locations"] if melter_check(configuration, row))


def required_copy(configuration: "SeedConfiguration", row: Mapping[str, Any]) -> int:
    if "tool_key" in row:
        return int(enabled(configuration))
    if enabled(configuration) and ("tool_level" in row or row["name"] == "Artefact Melter"):
        return 0
    if "tool_level" in row and not configuration.option("content_progression"):
        return 0
    if row["name"] == "Progressive Tools" and configuration.option("content_progression"):
        return 0
    if row["name"] == "Artefact Melter" and not (
        configuration.option("content_progression")
        and configuration.option("artefact_discovery_mode")
        and "checks_artefacts" in configuration.checks
        and (
            configuration.option("artefact_discovery_count") == 0
            or configuration.option("artefact_discovery_count") > 20
        )
    ):
        return 0
    return int(row.get("copies", 1))
