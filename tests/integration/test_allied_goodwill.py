from collections import Counter

import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.goodwill import ALLIED_NAME
from gamma_archipelago.presets import presets


@pytest.mark.parametrize("seed", [17, 118])
def test_allied_rewards_never_satisfy_hostile_settlement_rules_and_pool_is_beatable(seed):
    multi = setup_multiworld(GammaWorld, options=presets()["living_legend"], seed=seed)
    world = multi.worlds[1]
    hostile = {"Faction Goodwill: " + faction for faction in ("army", "bandit", "killer")}
    expected = {name: 5 for name in hostile} | {ALLIED_NAME: 12}
    assert (
        Counter(item.name for item in multi.itempool if item.name.startswith("Faction Goodwill:"))
        == expected
    )
    state = CollectionState(multi)
    for item in multi.itempool:
        if item.name not in hostile:
            state.collect(item, True)
    for faction, ids in (
        ("army", (28052103, 28052106)),
        ("bandit", (28052108,)),
        ("killer", (28052112,)),
    ):
        locations = [loc for loc in multi.get_locations() if loc.address in ids]
        assert all(not location.can_reach(state) for location in locations)
        for _ in range(4):
            state.collect(world.create_item("Faction Goodwill: " + faction), True)
        assert all(not location.can_reach(state) for location in locations)
        state.collect(world.create_item("Faction Goodwill: " + faction), True)
        assert all(location.can_reach(state) for location in locations)
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()
