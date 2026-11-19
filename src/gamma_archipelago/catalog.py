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
ALL_LOCATION_IDS = frozenset(LOCATION_NAMES.values())
# Public compatibility default for version 1/2 three-map seeds.
LOCATION_IDS = frozenset({28052001, 28052002, 28052003})
LEVELS: dict[str, str] = {level["id"]: level["name"] for level in _data["levels"]}
MAP_LOCATIONS: dict[str, int] = {loc["level"]: loc["id"] for loc in _data["locations"]}
CONNECTIONS: tuple[tuple[str, str], ...] = tuple(tuple(pair) for pair in _data["connections"])
MAX_ITEMS = 4000
MAX_SNAPSHOT_BYTES = 131072
