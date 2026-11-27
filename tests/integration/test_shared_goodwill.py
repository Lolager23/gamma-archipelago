from collections import Counter

import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.goodwill import SHARED_NAME
from gamma_archipelago.presets import presets


@pytest.mark.parametrize("seed", [17, 118])
def test_shared_pool_fills_without_self_locks_and_credits_each_faction(seed):
    multi = setup_multiworld(GammaWorld, options=presets()["living_legend"], seed=seed)
    world = multi.worlds[1]
    assert Counter(
        item.name for item in multi.itempool if item.name.startswith("Faction Goodwill:")
    ) == {SHARED_NAME: 12}
    state = CollectionState(multi)
    for item in multi.itempool:
        if item.name != SHARED_NAME:
            state.collect(item, True)
    bases = [
        location
        for location in multi.get_locations()
        if location.address in {28052103, 28052106, 28052108, 28052112}
    ]
    for _ in range(4):
        state.collect(world.create_item(SHARED_NAME), True)
    assert all(not location.can_reach(state) for location in bases)
    state.collect(world.create_item(SHARED_NAME), True)
    assert all(location.can_reach(state) for location in bases)
    final = multi.get_location("Faction Standing: 3000 Goodwill", 1)
    assert not final.can_reach(state)
    for _ in range(7):
        state.collect(world.create_item(SHARED_NAME), True)
    assert final.can_reach(state)
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()
    assert sum(len(sphere) for sphere in multi.get_spheres()) == len(multi.get_locations())
