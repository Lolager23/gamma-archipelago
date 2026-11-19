"""Catalogue-backed web planning and validated single-slot YAML documents."""

import json
import re
from collections import Counter
from collections.abc import Mapping
from importlib.resources import files
from typing import Any, cast

from .catalog import GAME, enabled_item_ids
from .configuration import (
    CHECK_OPTIONS,
    GEAR_OPTIONS,
    GOALS,
    QUANTITY_OPTIONS,
    REWARD_OPTIONS,
    build_configuration,
)
from .discovery import configured_location_ids
from .presets import presets
from .web_estimates import ASSUMPTIONS, estimate_playtime

LABELS = {
    "checks_shops": "Named trader purchases",
    "checks_faction_standing": "Faction goodwill milestones",
    "checks_maps": "Map arrivals",
    "checks_settlements": "Major settlements",
    "checks_mutant_first_kills": "First mutant kills",
    "checks_faction_first_kills": "First faction kills",
    "checks_artefacts": "Artefact collection",
    "checks_quest_types": "Quest types",
    "checks_gear_upgrades": "Gear upgrades",
    "checks_armour_tiers": "Armour weight tiers",
    "checks_weapon_tiers": "Weapon classes",
    "checks_knife_tiers": "Knife tiers",
    "checks_kill_milestones": "Kill totals",
    "checks_side_task_milestones": "Side-task totals",
    "checks_story_milestones": "Story milestones",
    "checks_rank_milestones": "Stalker rank",
    "rewards_loot_stashes": "White loot stashes",
    "rewards_progression_stashes": "Orange progression stash",
    "rewards_quest_keys": "Quest progression keys",
    "rewards_faction_reputation": "Faction goodwill",
    "rewards_stat_levels": "Haruka skill levels",
    "rewards_zone_keys": "Zone access keys",
    "rewards_starting_gear_unlocks": "Equipment permissions",
}
GOAL_LABELS = (
    "Three-region tour",
    "Calibrated psi protection",
    "Disable Brain Scorcher",
    "Meet Strelok",
    "Finish Living Legend",
    "Visit all five X-Labs",
)


def catalogue() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8")),
    )


def metadata() -> dict[str, object]:
    data = catalogue()
    check_counts = Counter(row["category"] for row in data["locations"] if "quota_group" not in row)
    check_counts.update({"checks_kill_milestones": 4, "checks_side_task_milestones": 4})
    reward_counts = Counter(row.get("category") for row in data["items"])
    return {
        "game": GAME,
        "presets": presets(),
        "checks": [
            dict(key=key, label=LABELS[key], count=check_counts[key]) for key in CHECK_OPTIONS
        ],
        "rewards": [
            dict(key=key, label=LABELS[key], count=reward_counts[key]) for key in REWARD_OPTIONS
        ],
        "gear": list(GEAR_OPTIONS),
        "quantities": list(QUANTITY_OPTIONS),
        "goals": [dict(value=i, key=key, label=GOAL_LABELS[i]) for i, key in enumerate(GOALS)],
        "assumptions": {
            key: dict(default=default, minimum=minimum, maximum=maximum)
            for key, (default, minimum, maximum) in ASSUMPTIONS.items()
        },
        "levels": {row["id"]: row["name"] for row in data["levels"]},
    }


def player_document(name: object, values: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_ -]{1,16}", name):
        raise ValueError("Player name: use 1–16 letters, numbers, spaces, underscores or hyphens")
    name = name.strip()
    if not name:
        raise ValueError("Player name cannot be blank")
    if name.casefold() == "archipelago":
        raise ValueError("Player name Archipelago is reserved for the server")
    configuration = build_configuration(values)
    return {
        "name": name,
        "game": GAME,
        "requires": {"version": "0.6.8"},
        GAME: configuration.to_values(),
    }


def preview(values: Mapping[str, object], assumptions: Mapping[str, object]) -> dict[str, object]:
    configuration = build_configuration(values)
    data = catalogue()
    ids = configured_location_ids(configuration)
    checks = [dict(row) for row in data["locations"] if row["id"] in ids]
    for category, thresholds in (
        ("checks_kill_milestones", configuration.kill_milestones),
        ("checks_side_task_milestones", configuration.side_task_milestones),
    ):
        if category in configuration.checks:
            definition = data["milestones"][category]
            checks.extend(
                dict(
                    id=definition["base_id"] + count,
                    name=definition["name"].format(count=count),
                    category=category,
                    level="Menu",
                )
                for count in thresholds
            )
    item_ids = enabled_item_ids(configuration.rewards, configuration.gear)
    rewards = [dict(row) for row in data["items"] if row["id"] in item_ids]
    required = sum(row["classification"] == "progression" for row in rewards)
    if required > len(checks):
        raise ValueError("The selected check pool cannot hold required progression rewards")
    counts = Counter(row["category"] for row in checks)
    return {
        "configuration": configuration.to_values(),
        "digest": configuration.digest,
        "checks": checks,
        "rewards": rewards,
        "check_counts": dict(counts),
        "reward_counts": dict(Counter(row.get("category", "base_supplies") for row in rewards)),
        "network_checks": len(checks),
        "reward_types": len(rewards),
        "required_rewards": required,
        "reward_slots": len(checks),
        "estimates": estimate_playtime(configuration, counts, assumptions),
        "notes": [
            "Reward types are eligible IDs, not guaranteed quantities. Each check holds one item.",
            "Progression permissions occur once; remaining slots use randomized supply rewards.",
            "Zone keys stay local; other rewards can cross players in a multiworld.",
            "Local goal events do not consume network checks or reward slots.",
            "Fresh Loner/Cordon saves are the baseline. Expanded engine testing is pending.",
        ],
    }
