"""Explicit access requirements shared by entrances and activity checks."""

from typing import TYPE_CHECKING, Any

from BaseClasses import CollectionState

if TYPE_CHECKING:
    from . import GammaWorld


def apply_access_rules(world: "GammaWorld", catalog: dict[str, Any]) -> None:
    player = world.player
    gear = dict(world.configuration.gear)
    zone_items = {
        item["level"]: item["name"]
        for item in catalog["items"]
        if item.get("category") == "rewards_zone_keys"
    }
    zoned = "rewards_zone_keys" in world.configuration.rewards

    def enter(state: CollectionState, level: str) -> bool:
        if zoned and level != "l01_escape" and not state.has(zone_items[level], player):
            return False
        if level in {"l10_radar", "l10u_bunker", "l08u_brainlab"}:
            if "rewards_progression_stashes" in world.configuration.rewards:
                return state.has("Calibrated Psi Protection", player)
            return state.has("Calibrated Psi Protection", player) or state.can_reach_region(
                "l08_yantar", player
            )
        return True

    for region in world.multiworld.get_regions(player):
        for entrance in region.entrances:
            if region.name in zone_items:
                entrance.access_rule = lambda state, level=region.name: enter(state, level)
    definitions = {row["id"]: row for row in catalog["locations"]}
    for location in world.multiworld.get_locations(player):
        definition = definitions.get(location.address)
        if definition is None:
            if location.address is None:
                continue
            definition = {
                "category": "checks_kill_milestones"
                if location.address < 28120000
                else "checks_side_task_milestones",
                "level": "Menu",
            }
        category = definition["category"]
        required = []
        if category in {"checks_artefacts"}:
            required.append("detector")
        if category == "checks_armour_tiers":
            required.append("outfit")
        if category == "checks_weapon_tiers":
            required.append("firearms")
        if category == "checks_knife_tiers":
            required.append("melee")
        names = [
            "Equipment Unlock: " + ("PDA" if group == "pda" else group.title())
            for group in required
            if gear["starting_" + group] == 2
        ]
        previous = location.access_rule
        # Global activities deliberately wait for full zone access. This is a
        # conservative guarantee, not a claim that every species lives in Cordon.
        global_activity = zoned and definition["level"] == "Menu"
        combat = category in {
            "checks_mutant_first_kills",
            "checks_faction_first_kills",
            "checks_kill_milestones",
        }

        def activity(
            state, prior=previous, items=names, global_check=global_activity, fight=combat
        ):
            return (
                prior(state)
                and all(state.has(name, player) for name in items)
                and (
                    not global_check
                    or all(state.can_reach_region(level, player) for level in zone_items)
                )
                and (
                    not fight
                    or gear["starting_firearms"] != 2
                    or gear["starting_melee"] != 2
                    or state.has("Equipment Unlock: Firearms", player)
                    or state.has("Equipment Unlock: Melee", player)
                )
            )

        location.access_rule = activity
