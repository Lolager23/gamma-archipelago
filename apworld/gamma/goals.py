"""Local completion events are separate from network checks and reward slots."""

from BaseClasses import ItemClassification

from gamma_archipelago.catalog import LOCATION_IDS


def add_goal_events(world, regions, location_type, item_type):
    if world.configuration.goal != "pilot_tour":
        claim = location_type(
            world.player, "Obtain Calibrated Helmet from Sakharov", None, regions["l08_yantar"]
        )
        claim.place_locked_item(
            item_type(
                "Calibrated Psi Protection", ItemClassification.progression, None, world.player
            )
        )
        regions["l08_yantar"].locations.append(claim)
    if world.configuration.goal in {"brain_scorcher", "meet_strelok"}:
        shutdown = location_type(
            world.player, "Shut Down Brain Scorcher", None, regions["l10u_bunker"]
        )
        shutdown.access_rule = lambda state: state.has("Calibrated Psi Protection", world.player)
        shutdown.place_locked_item(
            item_type("Brain Scorcher Disabled", ItemClassification.progression, None, world.player)
        )
        regions["l10u_bunker"].locations.append(shutdown)
    if world.configuration.goal == "meet_strelok":
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


def set_goal_rule(world, catalog):
    if world.configuration.goal == "psi_protection":
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
    else:
        world.multiworld.completion_condition[world.player] = lambda state: all(
            state.can_reach_region(row["level"], world.player)
            for row in catalog["locations"]
            if row["id"] in LOCATION_IDS
        )
