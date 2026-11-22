import pytest
from BaseClasses import CollectionState, LocationProgressType
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.presets import presets


def test_paid_contracts_can_hold_progression_but_expensive_contracts_reject_gear():
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"])
    world = multi.worlds[1]
    shops = {
        loc.address: loc
        for loc in multi.get_locations()
        if loc.address and 28052921 <= loc.address <= 28052929
    }
    assert all(loc.progress_type != LocationProgressType.EXCLUDED for loc in shops.values())
    gear = world.create_item("Equipment Unlock: PDA")
    key = world.create_item("Zone Key: Garbage")
    assert shops[28052921].item_rule(gear)
    assert not shops[28052923].item_rule(gear)
    assert shops[28052923].item_rule(key)
    assert not next(loc for loc in multi.get_locations() if loc.address == 28052808).item_rule(gear)


def test_rank_and_high_gear_logic_require_ap_goodwill_or_a_northern_route():
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"])
    state = CollectionState(multi)
    for item in multi.itempool:
        if not item.name.startswith("Faction Goodwill:"):
            state.collect(item, True)
    rank = next(loc for loc in multi.get_locations() if loc.address == 28052808)
    assert not rank.can_reach(state)
    world = multi.worlds[1]
    for _ in range(12):
        state.collect(world.create_item("Faction Goodwill: stalker"), True)
    assert rank.can_reach(state)


@pytest.mark.generation
def test_practical_full_story_fills_without_self_locks():
    for seed in range(30):
        multi = setup_multiworld(GammaWorld, options=presets()["full_story"], seed=seed)
        distribute_items_restrictive(multi)
        assert multi.can_beat_game()
        assert sum(len(sphere) for sphere in multi.get_spheres()) == len(multi.get_locations())
