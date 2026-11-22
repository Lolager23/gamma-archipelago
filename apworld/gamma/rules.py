"""Explicit access requirements shared by entrances and activity checks."""

from typing import TYPE_CHECKING, Any

from BaseClasses import CollectionState

from gamma_archipelago.activity_requirements import regional_requirement
from gamma_archipelago.content_progression import melter_check, tool_level
from gamma_archipelago.equipment_classes import check_classes, count_with_aliases
from gamma_archipelago.equipment_classes import level as class_level
from gamma_archipelago.playability import allowed
from gamma_archipelago.progression_readiness import allowed as progression_allowed
from gamma_archipelago.progression_readiness import requirements as readiness_requirements
from gamma_archipelago.quest_routes import allowed as quest_allowed
from gamma_archipelago.settlement_access import requirement
from gamma_archipelago.starting import starting_level
from gamma_archipelago.tool_permissions import enabled as tool_permissions_enabled
from gamma_archipelago.tool_permissions import melter_item, required_tier

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
        if not quest_allowed(world.configuration, level, lambda name: state.count(name, player)):
            return False
        if (
            zoned
            and level not in {"l01_escape", starting_level(world.configuration)}
            and not state.has(zone_items[level], player)
        ):
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
                story = catalog["story_goal_checks"].get(location.name)
                if story is None and (
                    world.configuration.option("quest_zone_logic")
                    or world.configuration.option("regional_progression")
                ):
                    story = catalog["quest_zone_gates"]["event_checks"].get(location.name)
                if story is None:
                    continue
                definition = definitions[story]
            else:
                definition = {
                    "category": "checks_kill_milestones"
                    if location.address < 28120000
                    else "checks_side_task_milestones",
                    "level": "Menu",
                    "minimum": location.address
                    - (28100000 if location.address < 28120000 else 28120000),
                }
        category = definition["category"]
        required = []
        if category in {"checks_artefacts"}:
            required.append("detector")
            if melter_check(world.configuration, definition) and not tool_permissions_enabled(
                world.configuration
            ):
                required.append("tools")
        if category in {
            "checks_quest_types",
            "checks_side_task_milestones",
            "checks_story_milestones",
        }:
            required.append("pda")
        if category == "checks_armour_tiers":
            required.append("outfit")
        if category == "checks_weapon_tiers":
            required.append("firearms")
        if category == "checks_knife_tiers":
            required.append("melee")
        if category == "checks_gear_upgrades":
            required.append("tools")
        names = [
            "Equipment Unlock: " + ("PDA" if group == "pda" else group.title())
            for group in required
            if gear["starting_" + group] == 2
        ]
        if "rewards_quest_keys" in world.configuration.rewards:
            for task in definition.get("tasks", ()):
                gate = catalog["quest_gates"][task]
                permissions = catalog["quest_key_requirements"][gate]
                names.extend(
                    row["name"] for row in catalog["items"] if row.get("permission") in permissions
                )
        tool_tier = required_tier(world.configuration, definition)
        if "rewards_progressive_tools" in world.configuration.rewards:
            tool_tier = max(
                tool_tier, readiness_requirements(world.configuration, definition).get("tools", 0)
            )
        if (
            "rewards_progressive_tools" in world.configuration.rewards
            and category == "checks_gear_upgrades"
        ):
            tool_tier = 3
        if (
            category == "checks_gear_upgrades"
            and "rewards_workshop_access" in world.configuration.rewards
        ):
            names.append("Workshop Access: Upgrades")
        previous = location.access_rule
        regional = regional_requirement(definition, world.configuration)
        settlement = requirement(world.configuration, location.address)
        combat = category in {
            "checks_mutant_first_kills",
            "checks_faction_first_kills",
            "checks_kill_milestones",
        }
        combat = combat or (
            category == "checks_quest_types"
            and definition["key"]
            in {"hunting", "bounty", "rescue", "defence", "assault", "territory", "vehicle"}
        )
        combat = combat or definition.get("logic", {}).get("combat", False)
        readiness = world.configuration.option("combat_logic")
        if combat and readiness:
            groups = ("firearms",) if readiness == 1 else ("firearms", "outfit", "helmet")
            names.extend(
                "Equipment Unlock: " + group.title()
                for group in groups
                if gear["starting_" + group] == 2
            )
        earning = (
            category in {"checks_rank_milestones", "checks_faction_standing"}
            and definition.get("minimum", 1) > 0
            and not (
                category == "checks_faction_standing"
                and world.configuration.option("playability_logic")
                and "rewards_faction_reputation" in world.configuration.rewards
            )
        )

        def activity(
            state,
            prior=previous,
            items=names,
            regional=regional,
            fight=combat,
            tools=tool_tier,
            earning=earning,
            settlement=settlement,
            definition=definition,
        ):
            def count(name):
                return state.count(name, player)

            permitted = count_with_aliases(world.configuration, count)
            owned_tools = tool_level(count) if tools else 0
            weapon = (
                gear["starting_firearms"] != 2
                or gear["starting_melee"] != 2
                or permitted("Equipment Unlock: Firearms")
                or permitted("Equipment Unlock: Melee")
            )
            return (
                prior(state)
                and allowed(
                    world.configuration,
                    definition,
                    permitted,
                    lambda level: state.can_reach_region(level, player),
                )
                and (settlement is None or state.has(settlement.name, player, settlement.copies))
                and (not tools or owned_tools >= tools)
                and progression_allowed(
                    world.configuration,
                    definition,
                    count,
                    lambda level: state.can_reach_region(level, player),
                    owned_tools,
                )
                and (
                    not melter_check(world.configuration, definition)
                    or "rewards_artefact_melter" not in world.configuration.rewards
                    or state.has(melter_item(world.configuration), player)
                )
                and all(permitted(name) for name in items)
                and all(
                    class_level(world.configuration, group, count) >= tier
                    for group, tier in check_classes(world.configuration, definition).items()
                )
                and regional.accessible(lambda level: state.can_reach_region(level, player))
                and (not fight or weapon)
                and (
                    not earning
                    or weapon
                    or gear["starting_pda"] != 2
                    or state.has("Equipment Unlock: PDA", player)
                )
            )

        location.access_rule = activity
