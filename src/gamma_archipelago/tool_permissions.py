"""Tool-use capabilities are AP receipts; ordinary copies never grant permission."""

import json
from collections.abc import Callable, Mapping
from importlib.resources import files
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

_catalog = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
TOOL_ITEMS = {row["tool_key"]: row["name"] for row in _catalog["items"] if "tool_key" in row}
TOOL_ITEM_IDS = frozenset(row["id"] for row in _catalog["items"] if "tool_key" in row)
TOOL_TIERS = tuple(TOOL_ITEMS[key] for key in ("basic", "advanced", "expert"))
TOOL_CAPABILITIES = tuple("Usable " + name.split(": ", 1)[1] for name in TOOL_TIERS)
REPAIR_TIERS = {"A": 0, "B": 1, "C": 2, "D": 3}


def enabled(configuration: "SeedConfiguration") -> bool:
    return bool(
        configuration.option("content_progression") and configuration.option("tool_use_permissions")
    )


def generic(configuration: "SeedConfiguration") -> bool:
    return enabled(configuration) and bool(configuration.option("progressive_tool_receipts"))


def level(count: Callable[[str], int]) -> int:
    result = 0
    for tier, name in enumerate(TOOL_CAPABILITIES, 1):
        if not count(name):
            break
        result = tier
    return result


def required_tier(configuration: "SeedConfiguration", row: Mapping[str, Any]) -> int:
    if not enabled(configuration) or "rewards_progressive_tools" not in configuration.rewards:
        return 0
    from .equipment_classes import repair_tier

    return max(
        REPAIR_TIERS.get(str(row.get("weapon_grade", "")), 0), repair_tier(configuration, row)
    )


def melter_item(configuration: "SeedConfiguration") -> str:
    return TOOL_ITEMS["artefact"] if enabled(configuration) else "Artefact Melter"
