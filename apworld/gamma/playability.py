"""Location placement restrictions for the local world's practical opening."""

from typing import TYPE_CHECKING

from gamma_archipelago.catalog import KILL_MILESTONE_BASE, SIDE_TASK_MILESTONE_BASE
from gamma_archipelago.playability import NORTH, early_check, late_equipment
from gamma_archipelago.starting import starting_level

if TYPE_CHECKING:
    from . import GammaWorld


def restrict_placements(world: "GammaWorld", catalog: dict) -> None:
    if not world.configuration.option("playability_logic") or world.configuration.checks <= {
        "checks_maps"
    }:
        return
    regions = {starting_level(world.configuration)}
    for _ in range(2):
        regions |= {
            end
            for a, b in catalog["connections"]
            for start, end in ((a, b), (b, a))
            if start in regions
        }
    regions -= {"l10_radar", "l10u_bunker", "l08u_brainlab", "l10_red_forest"}
    equipment = {
        row["id"]
        for row in catalog["items"]
        if row.get("category") == "rewards_starting_gear_unlocks"
    }
    definitions = {row["id"]: row for row in catalog["locations"]}
    for location in world.multiworld.get_locations(world.player):
        if not location.address:
            continue
        row = definitions.get(location.address)
        if row is None:
            base = (
                KILL_MILESTONE_BASE
                if location.address < SIDE_TASK_MILESTONE_BASE
                else SIDE_TASK_MILESTONE_BASE
            )
            row = {
                "level": "Menu",
                "category": "checks_kill_milestones"
                if base == KILL_MILESTONE_BASE
                else "checks_side_task_milestones",
                "minimum": location.address - base,
            }
        early = early_check(row, frozenset(regions))
        previous = location.item_rule
        location.item_rule = lambda item, prior=previous, early=early: (
            prior(item) and (item.code not in equipment or early)
        )


def restrict_tool_stashes(world: "GammaWorld", catalog: dict) -> None:
    if not world.configuration.option("content_progression"):
        return
    definitions = {row["id"]: row for row in catalog["locations"]}
    tiers = {
        row["id"]: row.get("kit_tier", row.get("tool_level"))
        for row in catalog["items"]
        if "tool_level" in row or "kit_tier" in row
    }
    middle = {"l03_agroprom", "l05_bar", "l06_rostok", "l08_yantar", "l07_military"}
    for location in world.multiworld.get_locations(world.player):
        row = definitions.get(location.address)
        if row is None:
            continue
        routes = set(row.get("logic", {}).get("all_regions", ())) | {row["level"]}
        medium = bool(routes & middle) or (
            row["category"] == "checks_rank_milestones" and row["minimum"] >= 5999
        )
        expert = (
            bool(routes & set(NORTH))
            or late_equipment(row)
            or (row["category"] == "checks_rank_milestones" and row["minimum"] >= 34999)
        )
        previous = location.item_rule
        location.item_rule = lambda item, prior=previous, medium=medium, expert=expert: (
            prior(item)
            and (
                item.code not in tiers
                or tiers[item.code] == 1
                or (tiers[item.code] == 2 and medium)
                or (tiers[item.code] == 3 and expert)
            )
        )
