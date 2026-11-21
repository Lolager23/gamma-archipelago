import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld
from worlds.gamma import GammaWorld


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_carried_firearms_can_be_upgraded_but_need_tool_workshop_permissions(mode):
    multiworld = setup_multiworld(
        GammaWorld,
        options=dict(
            checks_gear_upgrades=1,
            starting_firearms=mode,
            rewards_starting_gear_unlocks=int(mode == 2),
            rewards_progressive_tools=1,
            rewards_workshop_access=1,
        ),
    )
    world = multiworld.worlds[1]
    state = CollectionState(multiworld)
    check = next(row for row in multiworld.get_locations() if row.address == 28052731)
    assert not check.access_rule(state)
    for _ in range(3):
        state.collect(world.create_item("Progressive Tools"))
    state.collect(world.create_item("Workshop Access: Upgrades"))
    assert check.access_rule(state)
    state.collect(world.create_item("Equipment Unlock: Melee"))
    assert check.access_rule(state)
    state.collect(world.create_item("Equipment Unlock: Firearms"))
    assert check.access_rule(state)


@pytest.mark.parametrize("outfit,helmet", [(0, 2), (1, 2), (2, 0), (2, 1), (2, 2)])
@pytest.mark.parametrize("unlock", ["Outfit", "Helmet"])
def test_carried_armour_can_be_upgraded_before_equipping_is_unlocked(outfit, helmet, unlock):
    multiworld = setup_multiworld(
        GammaWorld,
        options=dict(
            checks_gear_upgrades=1,
            starting_outfit=outfit,
            starting_helmet=helmet,
            rewards_starting_gear_unlocks=1,
        ),
    )
    world = multiworld.worlds[1]
    state = CollectionState(multiworld)
    check = next(row for row in multiworld.get_locations() if row.address == 28052734)
    assert check.access_rule(state)
    state.collect(world.create_item("Equipment Unlock: " + unlock))
    assert check.access_rule(state)
