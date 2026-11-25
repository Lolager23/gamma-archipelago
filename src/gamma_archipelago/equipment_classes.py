"""Cumulative use permissions; physical gear remains ordinary GAMMA inventory."""

import json
from collections.abc import Callable, Mapping
from importlib.resources import files
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

_catalog = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
GROUPS = _catalog["equipment_classes"]["groups"]
ITEMS = {row["item_name"]: group for group, row in GROUPS.items()}
LEGACY = {row["legacy"]: group for group, row in GROUPS.items()}
RETIRED = frozenset({*LEGACY, "Equipment Unlock: Melee", "Equipment Unlock: Tools"})


def contract(configuration: "SeedConfiguration") -> bool:
    return bool(configuration.option("equipment_class_progression"))


def enabled(configuration: "SeedConfiguration") -> bool:
    return contract(configuration) and "rewards_starting_gear_unlocks" in configuration.rewards


def level(configuration: "SeedConfiguration", group: str, count: Callable[[str], int]) -> int:
    row = GROUPS[group]
    maximum = len(row["labels"])
    if enabled(configuration):
        return min(maximum, configuration.option(row["option"]) + count(row["item_name"]))
    locked = dict(configuration.gear)["starting_" + group] == 2
    return 0 if locked and not count(row["legacy"]) else maximum


def count_with_aliases(
    configuration: "SeedConfiguration", count: Callable[[str], int]
) -> Callable[[str], int]:
    def current(name: str) -> int:
        if contract(configuration) and name == "Equipment Unlock: Melee":
            return 1
        if contract(configuration) and name == "Equipment Unlock: Tools":
            return 1
        if enabled(configuration) and name in LEGACY:
            return int(level(configuration, LEGACY[name], count) >= 1)
        return count(name)

    return current


def item_enabled(configuration: "SeedConfiguration", row: Mapping[str, Any]) -> bool:
    if "class_group" in row:
        return enabled(configuration)
    return not (contract(configuration) and row["name"] in RETIRED)


def required_copies(configuration: "SeedConfiguration", row: Mapping[str, Any]) -> int:
    definition = GROUPS[row["class_group"]]
    return max(0, len(definition["labels"]) - configuration.option(definition["option"]))


def baseline_rewards(configuration: "SeedConfiguration") -> frozenset[str]:
    if not enabled(configuration):
        return frozenset()
    return frozenset(
        row["item_name"] for row in GROUPS.values() if configuration.option(row["option"]) == 0
    )


def check_classes(configuration: "SeedConfiguration", row: Mapping[str, Any]) -> dict[str, int]:
    if not contract(configuration):
        return {}
    category = row.get("category")
    if category == "checks_armour_tiers":
        return {"outfit": int(row["key"]) + 1}
    if category == "checks_weapon_tiers":
        grade = row.get("weapon_grade")
        tier = (
            ord(grade) - ord("A") + 1
            if grade
            else _catalog["equipment_classes"]["weapon_role_minimum"][row["key"]]
        )
        return {"firearms": tier}
    return {}
