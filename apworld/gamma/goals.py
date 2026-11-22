"""Local completion events are separate from network checks and reward slots."""

from typing import TYPE_CHECKING, Any

from BaseClasses import Item, ItemClassification, Location, Region

from gamma_archipelago.catalog import LOCATION_IDS

if TYPE_CHECKING:
    from . import GammaWorld


def add_goal_events(
    world: "GammaWorld",
    regions: dict[str, Region],
    location_type: type[Location],
    item_type: type[Item],
) -> None:
    if (
        world.configuration.goal not in {"pilot_tour", "talk_sidorovich"}
        or world.configuration.option("quest_zone_logic")
        or world.configuration.option("regional_progression")
        or (
            world.configuration.option("playability_logic")
            and bool(world.configuration.checks & {"checks_armour_tiers", "checks_weapon_tiers"})
        )
    ) and "rewards_progression_stashes" not in world.configuration.rewards:
        claim = location_type(
            world.player, "Obtain Calibrated Helmet from Sakharov", None, regions["l08_yantar"]
        )
        claim.place_locked_item(
            item_type(
                "Calibrated Psi Protection", ItemClassification.progression, None, world.player
            )
        )
        regions["l08_yantar"].locations.append(claim)
    if world.configuration.goal == "talk_sidorovich":
        conversation = location_type(
            world.player, "Talk to Sidorovich", None, regions["l01_escape"]
        )
        conversation.place_locked_item(
            item_type("Talked to Sidorovich", ItemClassification.progression, None, world.player)
        )
        regions["l01_escape"].locations.append(conversation)
    if world.configuration.option("quest_zone_logic"):
        machine = location_type(
            world.player, "Disable Miracle Machine", None, regions["l08u_brainlab"]
        )
        machine.access_rule = lambda state: (
            dict(world.configuration.gear)["starting_pda"] != 2
            or state.has("Equipment Unlock: PDA", world.player)
        )
        machine.place_locked_item(
            item_type(
                "Miracle Machine Disabled", ItemClassification.progression, None, world.player
            )
        )
        regions["l08u_brainlab"].locations.append(machine)
    if (
        world.configuration.option("quest_zone_logic")
        or world.configuration.option("regional_progression")
        or world.configuration.goal
        in {
            "brain_scorcher",
            "meet_strelok",
            "living_legend",
            "mortal_sin",
            "operation_afterglow",
        }
    ):
        shutdown = location_type(
            world.player, "Shut Down Brain Scorcher", None, regions["l10u_bunker"]
        )
        shutdown.access_rule = lambda state: state.has("Calibrated Psi Protection", world.player)
        shutdown.place_locked_item(
            item_type("Brain Scorcher Disabled", ItemClassification.progression, None, world.player)
        )
        regions["l10u_bunker"].locations.append(shutdown)
    if world.configuration.goal in {
        "meet_strelok",
        "living_legend",
        "mortal_sin",
        "operation_afterglow",
    }:
        encounter = location_type(
            world.player, "Conclude Strelok's First Conversation", None, regions["pripyat"]
        )
        encounter.access_rule = lambda state: (
            state.has("Brain Scorcher Disabled", world.player)
            and (
                "rewards_quest_keys" not in world.configuration.rewards
                or state.has("Quest Key: Living Legend", world.player)
            )
            and all(
                state.can_reach_region(level, world.player)
                for level in (
                    "k00_marsh",
                    "l03u_agr_underground",
                    "zaton",
                    "jupiter",
                    "jupiter_underground",
                )
            )
        )
        encounter.place_locked_item(
            item_type("Met Strelok", ItemClassification.progression, None, world.player)
        )
        regions["pripyat"].locations.append(encounter)
    if world.configuration.goal in {"living_legend", "mortal_sin", "operation_afterglow"}:
        finish = location_type(
            world.player, "Return After Living Legend", None, regions["l01_escape"]
        )
        # The shared access pass adds this terminal story check's route/equipment.
        finish.access_rule = lambda state: state.has("Met Strelok", world.player)
        finish.place_locked_item(
            item_type("Living Legend Complete", ItemClassification.progression, None, world.player)
        )
        regions["l01_escape"].locations.append(finish)

    for goal, title, event, prerequisite in (
        ("mortal_sin", "Return After Mortal Sin", "Mortal Sin Complete", "Living Legend Complete"),
        (
            "operation_afterglow",
            "Finish Operation Afterglow",
            "Operation Afterglow Complete",
            "Mortal Sin Complete",
        ),
    ):
        if world.configuration.goal == goal or (
            goal == "mortal_sin" and world.configuration.goal == "operation_afterglow"
        ):
            finish = location_type(world.player, title, None, regions["l01_escape"])
            finish.access_rule = lambda state, prerequisite=prerequisite, goal=goal: (
                state.has(prerequisite, world.player)
                and (
                    "rewards_quest_keys" not in world.configuration.rewards
                    or state.has(
                        "Quest Key: Mortal Sin"
                        if goal == "mortal_sin"
                        else "Quest Key: Operation Afterglow",
                        world.player,
                    )
                )
            )
            finish.place_locked_item(
                item_type(event, ItemClassification.progression, None, world.player)
            )
            regions["l01_escape"].locations.append(finish)


def set_goal_rule(world: "GammaWorld", catalog: dict[str, Any]) -> None:
    if world.configuration.goal in {"mortal_sin", "operation_afterglow"}:
        event = (
            "Mortal Sin Complete"
            if world.configuration.goal == "mortal_sin"
            else "Operation Afterglow Complete"
        )
        world.multiworld.completion_condition[world.player] = lambda state: state.has(
            event, world.player
        )
    elif world.configuration.goal == "talk_sidorovich":
        world.multiworld.completion_condition[world.player] = lambda state: state.has(
            "Talked to Sidorovich", world.player
        )
    elif world.configuration.goal == "psi_protection":
        world.multiworld.completion_condition[world.player] = lambda state: state.has(
            "Calibrated Psi Protection", world.player
        )
    elif world.configuration.goal == "brain_scorcher":
        world.multiworld.completion_condition[world.player] = lambda state: state.has(
            "Brain Scorcher Disabled", world.player
        )
    elif world.configuration.goal == "meet_strelok":
        world.multiworld.completion_condition[world.player] = lambda state: state.has(
            "Met Strelok", world.player
        )
    elif world.configuration.goal == "living_legend":
        world.multiworld.completion_condition[world.player] = lambda state: state.has(
            "Living Legend Complete", world.player
        )
    elif world.configuration.goal == "all_x_labs":
        world.multiworld.completion_condition[world.player] = lambda state: (
            state.has("Calibrated Psi Protection", world.player)
            and all(state.can_reach_region(level, world.player) for level in catalog["x_labs"])
        )
    else:
        world.multiworld.completion_condition[world.player] = lambda state: all(
            state.can_reach_region(row["level"], world.player)
            for row in catalog["locations"]
            if row["id"] in LOCATION_IDS
        )
