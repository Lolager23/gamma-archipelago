"""Keys share upstream randomized placement instead of reserving map arrivals."""

import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from Options import OptionError
from test.general import setup_multiworld
from worlds.apquest.world import APQuestWorld
from worlds.gamma import GammaWorld
from worlds.generic.Rules import locality_rules

from gamma_archipelago.presets import presets


def zone_items(multiworld):
    return [
        item
        for item in multiworld.itempool
        if item.player == 1 and item.name.startswith("Zone Key:")
    ]


@pytest.mark.parametrize("mixed", [False, True])
def test_expanded_keys_are_unplaced_before_upstream_fill(mixed):
    types = [GammaWorld, APQuestWorld] if mixed else GammaWorld
    multiworld = setup_multiworld(types, options=presets()["full_story"], seed=12)
    assert len(zone_items(multiworld)) == 32
    assert all(item.location is None for item in zone_items(multiworld))
    distribute_items_restrictive(multiworld)
    assert multiworld.can_beat_game()
    assert any(
        item.location.name.find("First Arrival") < 0 or item.location.player != 1
        for item in zone_items(multiworld)
    )
    assert not any(item.location.locked for item in zone_items(multiworld))


@pytest.mark.parametrize("remote", [False, True])
def test_zone_keys_respect_common_locality_in_real_upstream_fill(remote):
    key = "Zone Key: Agroprom"
    options = {**presets()["full_story"], "non_local_items" if remote else "local_items": [key]}
    multiworld = setup_multiworld([GammaWorld, APQuestWorld], options=[options, {}], seed=11)
    locality_rules(multiworld)
    distribute_items_restrictive(multiworld)
    item = next(item for item in zone_items(multiworld) if item.name == key)
    assert (item.location.player != 1) == remote
    assert multiworld.can_beat_game()


def test_expanded_map_exclusion_is_honoured_without_forcing_a_route():
    options = {**presets()["full_story"], "exclude_locations": ["Cordon: First Arrival"]}
    multiworld = setup_multiworld(GammaWorld, options=options, seed=7)
    from worlds.generic.Rules import exclusion_rules

    exclusion_rules(multiworld, 1, options["exclude_locations"])
    distribute_items_restrictive(multiworld)
    item = multiworld.get_location("Cordon: First Arrival", 1).item
    assert not item.advancement and not item.useful
    assert multiworld.can_beat_game()


@pytest.mark.parametrize("gift", [False, True])
def test_hub_preference_requests_upstream_early_item_without_fixed_location(gift):
    from worlds.AutoWorld import call_all

    options = {**presets()["full_story"], "access_pacing": 1}
    multiworld = setup_multiworld(
        GammaWorld, options=options, steps=("generate_early", "create_regions")
    )
    world = multiworld.worlds[1]
    if gift:
        multiworld.push_precollected(world.create_item("Zone Key: Garbage"))
    for step in ("create_items", "set_rules", "pre_fill"):
        call_all(multiworld, step)
    expected = "Zone Key: Rostok" if gift else "Zone Key: Garbage"
    assert multiworld.early_items[1][expected] == 1
    assert (
        sum(
            count
            for name, count in multiworld.early_items[1].items()
            if name.startswith("Equipment Unlock:")
        )
        == 1
    )
    assert all(item.location is None for item in zone_items(multiworld))
    distribute_items_restrictive(multiworld)
    assert multiworld.can_beat_game()


def test_sparse_fallback_still_respects_item_rules():
    multiworld = setup_multiworld(
        GammaWorld,
        options={"rewards_zone_keys": 1},
        steps=("generate_early", "create_regions", "create_items", "set_rules"),
    )
    multiworld.get_location("Cordon: First Arrival", 1).item_rule = lambda item: False
    with pytest.raises(OptionError, match="item restrictions"):
        multiworld.worlds[1].pre_fill()


def test_sparse_hub_policy_preserves_a_reachable_chain_without_locking_checks():
    multiworld = setup_multiworld(GammaWorld, options={"rewards_zone_keys": 1, "access_pacing": 1})
    first = multiworld.get_location("Cordon: First Arrival", 1)
    assert first.item.name == "Zone Key: Garbage" and not first.locked
    distribute_items_restrictive(multiworld)
    state = CollectionState(multiworld)
    state.sweep_for_advancements()
    assert all(location.can_reach(state) for location in multiworld.get_locations())


def test_hub_preference_does_not_duplicate_precollected_hubs():
    from worlds.AutoWorld import call_all

    options = {**presets()["full_story"], "access_pacing": 1}
    multiworld = setup_multiworld(
        GammaWorld, options=options, steps=("generate_early", "create_regions")
    )
    world = multiworld.worlds[1]
    for hub in ("Garbage", "Rostok", "Yantar", "Agroprom", "Wild Territory"):
        multiworld.push_precollected(world.create_item("Zone Key: " + hub))
    for step in ("create_items", "set_rules", "pre_fill"):
        call_all(multiworld, step)
    assert not any(name.startswith("Zone Key:") for name in multiworld.early_items[1])


def test_early_hub_request_preserves_a_stronger_existing_upstream_request():
    from worlds.gamma.zone_fill import prefer_early_hub

    from gamma_archipelago.web_planner import catalogue

    multiworld = setup_multiworld(
        GammaWorld, options={**presets()["full_story"], "access_pacing": 1}
    )
    multiworld.early_items[1]["Zone Key: Garbage"] = 2
    prefer_early_hub(multiworld.worlds[1], catalogue())
    assert multiworld.early_items[1]["Zone Key: Garbage"] == 2


@pytest.mark.generation
def test_randomized_expanded_key_seeds_have_no_deadlocks_and_varied_placements():
    patterns = set()
    for seed in range(40):
        multiworld = setup_multiworld(GammaWorld, options=presets()["full_story"], seed=seed)
        distribute_items_restrictive(multiworld)
        state = CollectionState(multiworld)
        state.sweep_for_advancements()
        assert all(location.can_reach(state) for location in multiworld.get_locations())
        assert multiworld.can_beat_game()
        patterns.add(
            tuple(sorted((item.name, item.location.name) for item in zone_items(multiworld)))
        )
    assert len(patterns) == 40


@pytest.mark.generation
def test_sparse_multiworld_regression_seeds_keep_the_safe_fallback():
    for seed in (1, 4, 6, 9, 11, 18, 29, 30, 32, 37, 39, 40, 43, 44):
        multiworld = setup_multiworld(
            [GammaWorld, GammaWorld], options={"rewards_zone_keys": 1}, seed=seed
        )
        distribute_items_restrictive(multiworld)
        state = CollectionState(multiworld)
        state.sweep_for_advancements()
        assert all(location.can_reach(state) for location in multiworld.get_locations())
        assert multiworld.can_beat_game()
