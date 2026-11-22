import pytest
from BaseClasses import CollectionState, LocationProgressType
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.apquest.world import APQuestWorld
from worlds.gamma import GammaWorld

from gamma_archipelago.presets import presets


@pytest.mark.parametrize("playability", [0, 1])
@pytest.mark.parametrize("reputation", [0, 1])
@pytest.mark.parametrize("optional", [0, 1, 2])
def test_all_rank_checks_reject_progression_and_useful_items(playability, reputation, optional):
    multi = setup_multiworld(
        GammaWorld,
        options=presets()["full_story"]
        | {
            "playability_logic": playability,
            "rewards_faction_reputation": reputation,
            "optional_check_policy": optional,
        },
    )
    ranks = [loc for loc in multi.get_locations() if loc.name.startswith("Reach Stalker Rank:")]
    assert len(ranks) == 8
    state = multi.get_all_state(False)
    world = multi.worlds[1]
    for location in ranks:
        assert location.progress_type == LocationProgressType.EXCLUDED
        for name in ("Zone Key: Garbage", "Equipment Unlock: PDA", "Basic Toolkit"):
            item = world.create_item(name)
            assert item.advancement or item.useful
            assert not location.can_fill(state, item, False)
        assert location.can_fill(state, world.create_item("Bandage"), False)


@pytest.mark.parametrize("mixed", [False, True])
def test_rank_rewards_remain_filler_after_solo_and_mixed_world_fill(mixed):
    types = [GammaWorld, APQuestWorld] if mixed else GammaWorld
    multi = setup_multiworld(types, options=presets()["full_story"], seed=260)
    distribute_items_restrictive(multi)
    ranks = [loc for loc in multi.get_locations(1) if loc.name.startswith("Reach Stalker Rank:")]
    assert len(ranks) == 8
    assert all(not loc.item.advancement and not loc.item.useful for loc in ranks)
    assert multi.can_beat_game()
    assert sum(len(sphere) for sphere in multi.get_spheres()) == len(multi.get_locations())


def test_disabling_rank_checks_still_omits_the_category():
    multi = setup_multiworld(
        GammaWorld, options=presets()["full_story"] | {"checks_rank_milestones": 0}
    )
    assert not any(loc.name.startswith("Reach Stalker Rank:") for loc in multi.get_locations())


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
    for name in ("Repair", "Upgrades", "Crafting"):
        workshop = world.create_item("Workshop Access: " + name)
        assert shops[28052921].item_rule(workshop)
        assert not shops[28052923].item_rule(workshop)
        assert not multi.get_location("Reach Stalker Rank: Legend", 1).item_rule(workshop)


def test_rank_and_high_gear_logic_require_ap_goodwill_or_a_northern_route():
    multi = setup_multiworld(
        GammaWorld,
        options=presets()["full_story"],
        steps=("generate_early", "create_regions", "create_items", "set_rules"),
    )
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
