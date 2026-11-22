"""AP access rules must prevent mutant milestones from hiding their own gear."""

import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.presets import presets
from gamma_archipelago.tool_permissions import TOOL_CAPABILITIES, TOOL_TIERS


def maximum_without_tools(world):
    state = CollectionState(world.multiworld)
    for item in world.multiworld.itempool + [
        r.item for r in world.multiworld.get_filled_locations()
    ]:
        if item.name not in {*TOOL_TIERS, *TOOL_CAPABILITIES, "Progressive Tools"}:
            state.collect(item, True)
    return state


@pytest.mark.parametrize("classes", [0, 1])
def test_firearm_repair_class_a_is_available_without_basic_tools(classes):
    multi = setup_multiworld(
        GammaWorld, options=presets()["full_story"] | {"equipment_class_progression": classes}
    )
    state = maximum_without_tools(multi.worlds[1])
    assert not state.has("Progressive Tools", 1)
    assert multi.get_location("Use Firearm Repair Class: A", 1).can_reach(state)
    assert not multi.get_location("Use Firearm Repair Class: B", 1).can_reach(state)


@pytest.mark.parametrize("minimum,tier", [(10, 0), (11, 2), (15, 2), (16, 3), (25, 3)])
def test_mutant_milestones_require_their_tool_tier_in_actual_world_rules(minimum, tier):
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"])
    world = multi.worlds[1]
    state = maximum_without_tools(world)
    # Gear/routes/events are otherwise at maximum; only tool capability is withheld.
    check = multi.get_location(f"Discovery: {minimum} Distinct Mutant Types", 1)
    if tier:
        for _ in range(tier - 1):
            state.collect(world.create_item("Progressive Tools"), True)
        assert not check.can_reach(state)
        state.collect(world.create_item("Progressive Tools"), True)
    assert check.can_reach(state)
