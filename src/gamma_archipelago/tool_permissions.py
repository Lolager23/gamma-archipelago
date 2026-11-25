"""Tool-use capabilities are AP receipts; ordinary copies never grant permission."""

import json
from collections.abc import Callable
from importlib.resources import files
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

_catalog = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
TOOL_ITEMS = {row["tool_key"]: row["name"] for row in _catalog["items"] if "tool_key" in row}
TOOL_ITEM_IDS = frozenset(row["id"] for row in _catalog["items"] if "tool_key" in row)
TOOL_TIERS = tuple(TOOL_ITEMS[key] for key in ("basic", "advanced", "expert"))
TOOL_CAPABILITIES = tuple("Usable " + name.split(": ", 1)[1] for name in TOOL_TIERS)


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


def melter_item(configuration: "SeedConfiguration") -> str:
    return TOOL_ITEMS["artefact"] if enabled(configuration) else "Artefact Melter"
