"""Finite capability assumptions; native observations still establish actual checks."""

import json
from collections.abc import Callable, Mapping
from importlib.resources import files
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

_catalog = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
GOODWILL = tuple(row["name"] for row in _catalog["items"] if row.get("effect") == "reputation")
RANK_PROXY = dict(
    zip(
        (0, 3999, 5999, 9999, 15999, 23999, 34999, 49999),
        (0, 250, 500, 750, 1000, 1500, 2000, 3000),
        strict=True,
    )
)
KNIFE_MUTANTS = frozenset({"boar", "dog", "flesh", "cat", "tushkano"})
NORTH = (
    "jupiter",
    "zaton",
    "l11_pripyat",
    "pripyat",
    "l11_hospital",
    "l12_stancia",
    "l12_stancia_2",
    "l13_generators",
)


def firearm_required(row: Mapping[str, Any]) -> bool:
    category = row["category"]
    if category == "checks_kill_milestones":
        return int(row["minimum"]) > 25
    if category == "checks_faction_first_kills":
        return True
    if category == "checks_mutant_first_kills":
        return int(row["minimum"]) > 5 if "minimum" in row else row["key"] not in KNIFE_MUTANTS
    return False


def goodwill_required(row: Mapping[str, Any]) -> int:
    if row["category"] == "checks_rank_milestones":
        return RANK_PROXY[row["minimum"]]
    if row["category"] == "checks_faction_standing":
        return int(row["minimum"])
    return 0


def late_equipment(row: Mapping[str, Any]) -> bool:
    return (row["category"] == "checks_armour_tiers" and int(row["key"]) >= 3) or row.get(
        "weapon_grade"
    ) == "D"


def allowed(
    configuration: "SeedConfiguration",
    row: Mapping[str, Any],
    count: Callable[[str], int],
    reachable: Callable[[str], bool],
) -> bool:
    if not configuration.option("playability_logic"):
        return True
    if (
        firearm_required(row)
        and dict(configuration.gear)["starting_firearms"] == 2
        and not count("Equipment Unlock: Firearms")
    ):
        return False
    needed, late = goodwill_required(row), late_equipment(row)
    if not needed and not late:
        return True
    reputation = "rewards_faction_reputation" in configuration.rewards
    goodwill = max((count(name) * 250 for name in GOODWILL), default=0) if reputation else 0
    if reputation and goodwill < needed:
        return False
    if late:
        north = (
            count("Calibrated Psi Protection")
            and reachable("l10_red_forest")
            and any(reachable(level) for level in NORTH)
        )
        return bool(
            north or ("rewards_faction_reputation" in configuration.rewards and goodwill >= 2000)
        )
    return True


def protected(configuration: "SeedConfiguration") -> frozenset[int]:
    if (
        not configuration.option("playability_logic")
        or "rewards_faction_reputation" in configuration.rewards
    ):
        return frozenset()
    return frozenset(row["id"] for row in _catalog["locations"] if goodwill_required(row))


def fragile_ids(configuration: "SeedConfiguration") -> frozenset[int]:
    return frozenset(
        row["id"]
        for row in _catalog["locations"]
        if row.get("missable")
        and not (
            configuration.option("playability_logic") and row["category"] == "checks_shop_purchases"
        )
    )


def early_check(row: Mapping[str, Any], regions: frozenset[str]) -> bool:
    category = row["category"]
    if row.get("level") != "Menu":
        return row["level"] in regions and row.get("price", 0) < 15000
    if category in {
        "checks_gear_upgrades",
        "checks_armour_tiers",
        "checks_weapon_tiers",
        "checks_knife_tiers",
        "checks_faction_standing",
        "checks_story_milestones",
    }:
        return False
    ceilings = {
        "checks_artefacts": 5,
        "checks_mutant_first_kills": 5,
        "checks_kill_milestones": 25,
        "checks_side_task_milestones": 3,
        "checks_rank_milestones": 0,
    }
    if category in ceilings and row.get("minimum", 10000) > ceilings[category]:
        return False
    logic = row.get("logic", {})
    return all(level in regions for level in logic.get("all_regions", ())) and (
        not logic.get("any_regions") or bool(regions.intersection(logic["any_regions"]))
    )
