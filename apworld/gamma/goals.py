"""Local completion events are separate from network checks and reward slots."""

from BaseClasses import ItemClassification

from gamma_archipelago.catalog import LOCATION_IDS


def add_goal_events(world, regions, location_type, item_type):
    if world.configuration.goal == "psi_protection":
        claim = location_type(
            world.player, "Obtain Calibrated Helmet from Sakharov", None, regions["l08_yantar"]
        )
        claim.place_locked_item(
            item_type(
                "Calibrated Psi Protection", ItemClassification.progression, None, world.player
            )
        )
        regions["l08_yantar"].locations.append(claim)


def set_goal_rule(world, catalog):
    if world.configuration.goal == "psi_protection":
        world.multiworld.completion_condition[world.player] = lambda state: state.has(
            "Calibrated Psi Protection", world.player
        )
    else:
        world.multiworld.completion_condition[world.player] = lambda state: all(
            state.can_reach_region(row["level"], world.player)
            for row in catalog["locations"]
            if row["id"] in LOCATION_IDS
        )
