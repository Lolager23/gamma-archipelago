"""Location placement restrictions for the local world's practical opening."""

from typing import TYPE_CHECKING

from gamma_archipelago.catalog import KILL_MILESTONE_BASE, SIDE_TASK_MILESTONE_BASE
from gamma_archipelago.playability import early_check
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
    regions -= {"l10_radar", "l10u_bunker", "l08u_brainlab"}
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
