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
LOCATION_IDS = frozenset(LOCATION_NAMES.values())
MAX_ITEMS = 4000
MAX_SNAPSHOT_BYTES = 131072
