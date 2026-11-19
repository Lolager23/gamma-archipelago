"""Stable pilot IDs. The packaged JSON also generates the Lua and AP-world tables."""

import json
from importlib.resources import files

_data = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text(encoding="utf-8"))
GAME: str = _data["game"]
SCHEMA_VERSION: int = _data["schema_version"]
ITEM_SECTIONS: dict[int, str] = {item["id"]: item["section"] for item in _data["items"]}
ITEM_NAMES: dict[str, int] = {item["name"]: item["id"] for item in _data["items"]}
ITEM_EFFECTS: dict[int, str] = {item["id"]: item.get("effect", "item") for item in _data["items"]}
LOCATION_NAMES: dict[str, int] = {
    location["name"]: location["id"] for location in _data["locations"]
}
KILL_MILESTONE_BASE: int = _data["milestones"]["checks_kill_milestones"]["base_id"]
MAX_KILL_MILESTONE: int = _data["milestones"]["checks_kill_milestones"]["maximum"]
LOCATION_NAMES.update(
    {
        f"Defeat {count} Enemies": KILL_MILESTONE_BASE + count
        for count in range(1, MAX_KILL_MILESTONE + 1)
    }
)
ALL_LOCATION_IDS = frozenset(LOCATION_NAMES.values())
# Public compatibility default for version 1/2 three-map seeds.
LOCATION_IDS = frozenset({28052001, 28052002, 28052003})
LEVELS: dict[str, str] = {level["id"]: level["name"] for level in _data["levels"]}
MAP_LOCATIONS: dict[str, int] = {
    loc["level"]: loc["id"] for loc in _data["locations"] if loc["category"] == "checks_maps"
}
MAP_LOCATION_IDS = frozenset(MAP_LOCATIONS.values())
LOCATION_CATEGORIES: dict[int, str] = {loc["id"]: loc["category"] for loc in _data["locations"]}
CONNECTIONS: tuple[tuple[str, str], ...] = tuple(tuple(pair) for pair in _data["connections"])
MAX_ITEMS = 4000
MAX_SNAPSHOT_BYTES = 131072


def enabled_location_ids(
    checks: frozenset[str], kill_milestones: tuple[int, ...] = (10, 25, 50, 100)
) -> frozenset[int]:
    locations = frozenset(
        identity for identity, category in LOCATION_CATEGORIES.items() if category in checks
    )
    if "checks_kill_milestones" in checks:
        locations |= frozenset(KILL_MILESTONE_BASE + count for count in kill_milestones)
    return locations
