"""Reach every generated map through actual placed zone-key rewards."""

import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("seed", [1, 4, 5, 22])
def test_zone_key_generation_has_no_circular_or_unreachable_map_rewards(seed):
    multiworld = setup_multiworld(GammaWorld, seed=seed, options={"rewards_zone_keys": 1})
    distribute_items_restrictive(multiworld)
    state = CollectionState(multiworld)
    state.sweep_for_advancements()
    assert all(location.can_reach(state) for location in multiworld.get_locations(1))
    assert multiworld.can_beat_game()
