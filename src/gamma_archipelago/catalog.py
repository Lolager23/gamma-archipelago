"""Stable pilot IDs. The packaged JSON also generates the Lua and AP-world tables."""

import json
from importlib.resources import files

_data = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text(encoding="utf-8"))
GAME: str = _data["game"]
SCHEMA_VERSION: int = _data["schema_version"]
POST_RED_FOREST_REGIONS = tuple(_data["post_red_forest_regions"])
ITEM_SECTIONS: dict[int, str] = {
    item["id"]: item["section"] for item in _data["items"] if "section" in item
}
ITEM_IDS = frozenset(item["id"] for item in _data["items"])
CLASS_ITEM_IDS = frozenset(item["id"] for item in _data["items"] if "class_group" in item)
ITEM_CATEGORIES: dict[int, str | None] = {
    item["id"]: item.get("category") for item in _data["items"]
}
ITEM_NAMES: dict[str, int] = {item["name"]: item["id"] for item in _data["items"]}
ITEM_GEAR: dict[int, str] = {
    item["id"]: item["group"] for item in _data["items"] if "group" in item
}
ITEM_EFFECTS: dict[int, str] = {item["id"]: item.get("effect", "item") for item in _data["items"]}
LOCATION_NAMES: dict[str, int] = {
    location["name"]: location["id"] for location in _data["locations"]
}
KILL_MILESTONE_BASE: int = _data["milestones"]["checks_kill_milestones"]["base_id"]
MAX_KILL_MILESTONE: int = _data["milestones"]["checks_kill_milestones"]["maximum"]
SIDE_TASK_MILESTONE_BASE: int = _data["milestones"]["checks_side_task_milestones"]["base_id"]
MAX_SIDE_TASK_MILESTONE: int = _data["milestones"]["checks_side_task_milestones"]["maximum"]
LOCATION_NAMES.update(
    {
        _data["milestones"]["checks_kill_milestones"]["name"].format(
            count=count
        ): KILL_MILESTONE_BASE + count
        for count in range(1, MAX_KILL_MILESTONE + 1)
    }
)
LOCATION_NAMES.update(
    {
        _data["milestones"]["checks_side_task_milestones"]["name"].format(
            count=count
        ): SIDE_TASK_MILESTONE_BASE + count
        for count in range(1, MAX_SIDE_TASK_MILESTONE + 1)
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


def enabled_item_ids(
    rewards: frozenset[str], gear: tuple[tuple[str, int], ...] | None = None
) -> frozenset[int]:
    modes = dict(gear or ())
    return frozenset(
        identity
        for identity, category in ITEM_CATEGORIES.items()
        if identity not in CLASS_ITEM_IDS
        if category is None or category in rewards
        if gear is None
        or identity not in ITEM_GEAR
        or modes.get("starting_" + ITEM_GEAR[identity]) == 2
    )


def enabled_location_ids(
    checks: frozenset[str],
    kill_milestones: tuple[int, ...] = (10, 25, 50, 100),
    side_task_milestones: tuple[int, ...] = (5, 10, 20, 40),
) -> frozenset[int]:
    locations = frozenset(
        row["id"]
        for row in _data["locations"]
        if row["category"] in checks and "quota_group" not in row
    )
    if "checks_kill_milestones" in checks:
        locations |= frozenset(KILL_MILESTONE_BASE + count for count in kill_milestones)
    if "checks_side_task_milestones" in checks:
        locations |= frozenset(SIDE_TASK_MILESTONE_BASE + count for count in side_task_milestones)
    return locations
