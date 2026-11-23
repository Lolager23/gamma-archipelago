"""Weighted non-progression supplies after mandatory and requested copies are reserved."""

import json
from functools import lru_cache
from importlib.resources import files
from typing import TYPE_CHECKING

from .content_progression import configured_item_ids

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

_items = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))["items"]


@lru_cache(maxsize=128)
def candidates(configuration: "SeedConfiguration") -> tuple[tuple[str, int], ...]:
    """Disabled categories stay absent, including upstream filler replacement."""
    if not configuration.option("varied_filler"):
        return (("Bandage", 1),)
    enabled = configured_item_ids(configuration)
    rows = tuple(
        (row["name"], int(row.get("filler_weight", 1)))
        for row in _items
        if row["id"] in enabled
        and row["classification"] == "filler"
        and (row.get("filler_family") or row.get("effect") == "loot_stash")
    )
    return rows or (("Medkit", 1), ("Bandage", 1))
