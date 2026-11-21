import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.presets import presets
from gamma_archipelago.starting import STARTS, starting_level


@pytest.mark.parametrize("location", range(4))
@pytest.mark.parametrize("seed", [0, 3, 19])
def test_full_story_start_and_zone_chain_fill_from_each_supported_root(location, seed):
    multiworld = setup_multiworld(
        GammaWorld, seed=seed, options={**presets()["full_story"], "starting_location": location}
    )
    world = multiworld.worlds[1]
    actual = world.configuration.option("starting_location")
    assert 0 <= actual < 3
    if location != 3:
        assert actual == location
    root = STARTS[actual]["level"]
    state = CollectionState(multiworld)
    assert state.can_reach_region(root, 1)
    assert world.multiworld.get_region("Menu", 1).exits[0].connected_region.name == root
    distribute_items_restrictive(multiworld)
    assert multiworld.can_beat_game()
    complete = multiworld.get_all_state()
    complete.sweep_for_advancements()
    assert all(loc.can_reach(complete) for loc in multiworld.get_locations())
    assert world.fill_slot_data()["configuration"]["starting_location"] == actual
    assert starting_level(world.configuration) == root


def test_random_start_is_seed_deterministic_and_only_free_stalkers_are_supported():
    from Options import OptionError

    first = setup_multiworld(GammaWorld, seed=42, options={"starting_location": 3}).worlds[1]
    second = setup_multiworld(GammaWorld, seed=42, options={"starting_location": 3}).worlds[1]
    assert first.configuration.digest == second.configuration.digest
    assert first.configuration.option("ap_start") == 1
    with pytest.raises((OptionError, KeyError, ValueError)):
        setup_multiworld(GammaWorld, options={"starting_faction": "monolith"})


@pytest.mark.generation
@pytest.mark.parametrize("location", range(4))
def test_one_hundred_full_story_seeds_for_each_fixed_and_random_start(location):
    from test_generation_matrix import assert_seed

    for seed in range(100):
        assert_seed({**presets()["full_story"], "starting_location": location}, seed)
