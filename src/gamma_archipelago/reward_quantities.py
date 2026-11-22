"""Deterministic repeatable reward requests; permissions are budgeted separately."""

import json
from collections import Counter
from importlib.resources import files
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

_data = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
GROUPS = {
    "artefact_rewards": ("rewards_artefacts", None),
    "basic_toolkits": ("base", None),
    "medical_packages": ("rewards_supply_medical", None),
    "maintenance_packages": ("rewards_supply_maintenance", None),
    "ammunition_packages": ("rewards_supply_ammunition", None),
    "expedition_packages": ("rewards_supply_expedition", None),
    "basic_loot_stashes": ("rewards_loot_stashes", "Basic"),
    "field_loot_stashes": ("rewards_loot_stashes", "Field"),
    "advanced_loot_stashes": ("rewards_loot_stashes", "Advanced"),
    "extra_faction_goodwill": ("rewards_faction_reputation", None),
    "stat_level_rewards": ("rewards_stat_levels", None),
}
DEFAULT_COUNTS = {name: (0 if name == "extra_faction_goodwill" else 4) for name in GROUPS}
DEFAULT_COUNTS["stat_level_rewards"] = 9
DEFAULT_COUNTS["basic_toolkits"] = 0


def requested(configuration: "SeedConfiguration") -> Counter[str]:
    result: Counter[str] = Counter()
    if not configuration.option("reward_quantities"):
        return result
    for key, (category, tier) in GROUPS.items():
        if category != "base" and category not in configuration.rewards:
            continue
        candidates = [
            row["name"]
            for row in _data["items"]
            if (
                row["name"] == "Basic Toolkit"
                if category == "base"
                else row.get("category") == category
            )
            and (tier is None or row["name"].startswith(tier + " Loot Stash:"))
        ]
        for index in range(configuration.option(key)):
            result[candidates[index % len(candidates)]] += 1
    return result


def useful_count(names: Counter[str]) -> int:
    filler = {row["name"] for row in _data["items"] if row["classification"] == "filler"}
    return sum(count for name, count in names.items() if name not in filler)
