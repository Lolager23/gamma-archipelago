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
from .discovery import SOURCES, configured_location_ids
from .opening import opening_permissions
from .presets import presets
from .settings_ui import advanced_options
from .settlement_access import NEUTRALITY_ITEMS
from .starting import STARTS
from .starting_unlock import preview_budget
from .web_estimates import ASSUMPTIONS, estimate_playtime

LABELS = {
    "rewards_convenience": "Bounded carry capacity",
    "rewards_supply_medical": "Medical Supply Package",
    "rewards_supply_maintenance": "Maintenance Supply Package",
    "rewards_supply_ammunition": "Ammunition Supply Package",
    "rewards_supply_expedition": "Expedition Supply Package",
    "rewards_workshop_access": "Workshop action permissions",
    "rewards_recipe_access": "Recipe group permissions",
    "rewards_progressive_tools": "Progressive workshop tools",
    "checks_shops": "First ordinary trader purchases",
    "checks_shop_purchases": "Buy Archipelago shop contracts (75,000 RU total)",
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
    "Talk to Sidorovich (quick pilot)",
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
        "advanced": advanced_options(),
        "discovery_types": [
            {"token": token, "group": group}
            for group, roster in SOURCES.items()
            for token in roster
        ],
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
    configuration = build_configuration({**values, "ap_start": 1})
    return {
        "name": name,
        "game": GAME,
        "requires": {"version": "0.6.8"},
        GAME: configuration.to_values(),
    }


def preview(values: Mapping[str, object], assumptions: Mapping[str, object]) -> dict[str, object]:
    configuration = build_configuration({**values, "ap_start": 1})
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
    budget, budget_report = preview_budget(configuration, ids)
    for reward in rewards:
        if (
            reward["name"] in NEUTRALITY_ITEMS
            and configuration.option("settlement_reputation_logic")
            and "checks_settlements" in configuration.checks
        ) or (
            reward.get("effect") == "reputation"
            and configuration.option("playability_logic")
            and bool(configuration.checks & {"checks_rank_milestones", "checks_faction_standing"})
        ):
            reward["classification"] = "progression"
    required = len(budget.required)
    counts = Counter(row["category"] for row in checks)
    shop_cost = sum(row.get("price", 0) for row in checks)
    return {
        "configuration": configuration.to_values(),
        "preview_kind": "settings_only",
        "pool_budget": budget_report,
        "opening_permissions": list(opening_permissions(configuration, dict(budget.starting))),
        "resolved_thresholds": {
            "kills": list(configuration.kill_milestones),
            "side_tasks": list(configuration.side_task_milestones),
        },
        "discovery_rosters": {
            group: {
                "qualifying": len(set(roster) - set(configuration.discovery_exclusions)),
                "excluded": sorted(set(roster) & set(configuration.discovery_exclusions)),
            }
            for group, roster in SOURCES.items()
        },
        "digest": configuration.digest,
        "checks": checks,
        "rewards": rewards,
        "check_counts": dict(counts),
        "reward_counts": dict(Counter(row.get("category", "base_supplies") for row in rewards)),
        "network_checks": len(checks),
        "reward_types": len(rewards),
        "required_rewards": required,
        "shop_cost_ru": shop_cost,
        "reward_slots": len(checks),
        "estimates": estimate_playtime(configuration, counts, assumptions),
        "notes": [
            "AP start: Free Stalkers / "
            + (
                STARTS[configuration.option("starting_location")]["name"]
                if configuration.option("starting_location") < len(STARTS)
                else "Random native preset (seed-fixed; preview budgets use Cordon)"
            ),
            "Reward types are eligible IDs, not guaranteed quantities. Each check holds one item.",
            "Required progression is budgeted first; progressive tools need three copies.",
            "Missable exclusions accept filler only. Convenience has a capped useful allocation.",
            "Protected opening reserves reliable Cordon checks for a fresh Loner/Cordon start.",
            "Settings preview only. Actual-seed JSON is optional; placement mode reveals spoilers.",
            "Zone keys use Archipelago fill and can cross players; local/non-local settings apply.",
            "Local goal events do not consume network checks or reward slots.",
            "Generic discovery tails accept filler only; repeated types do not advance checks.",
            *(
                [
                    "Random starting permission is unresolved here; per-choice budgets are shown "
                    "and opening requirements use the most demanding roll."
                ]
                if configuration.option("random_starting_unlock")
                else []
            ),
            "Fresh Loner/Cordon saves are the baseline. Expanded engine testing is pending.",
            *(
                [
                    f"Selected AP contracts cost {shop_cost:,} RU total; "
                    "income-grind time is uncalibrated."
                ]
                if shop_cost
                else []
            ),
        ],
    }
