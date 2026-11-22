import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld
from worlds.gamma.analysis import analyse

from gamma_archipelago.equipment_classes import GROUPS
from gamma_archipelago.presets import presets


def maximum(world, missing=(), counts=None):
    state = CollectionState(world.multiworld)
    special = {row["item_name"] for row in GROUPS.values()} | {"Progressive Tools"}
    network = world.multiworld.itempool + [
        row.item for row in world.multiworld.get_filled_locations() if row.address is not None
    ]
    for item in network:
        if item.name not in set(missing) and (counts is None or item.name not in special):
            state.collect(item, True)
    for name, count in (counts or {}).items():
        for _ in range(count):
            state.collect(world.create_item(name), True)
    state.sweep_for_advancements()
    return state


@pytest.mark.parametrize(
    "name", ["Progressive Firearm Class", "Progressive Outfit Class", "Progressive Tools"]
)
def test_scorcher_requires_advanced_medium_and_class_c_even_with_all_keys_and_goodwill(name):
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"])
    world = multi.worlds[1]
    counts = {"Progressive Firearm Class": 2, "Progressive Outfit Class": 2, "Progressive Tools": 2}
    counts[name] = 1
    state = maximum(world, counts=counts)
    assert not multi.get_location("Story: Living Legend / Turn Off Brain Scorcher", 1).can_reach(
        state
    )
    assert not state.has("Brain Scorcher Disabled", 1)
    assert not state.can_reach_region("l13_generators", 1)
    state.collect(world.create_item(name), True)
    state.sweep_for_advancements()
    assert state.has("Brain Scorcher Disabled", 1)


@pytest.mark.parametrize(
    "name", ["Progressive Firearm Class", "Progressive Outfit Class", "Progressive Tools"]
)
def test_path_pripyat_requires_expert_heavy_and_class_d(name):
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"])
    world = multi.worlds[1]
    counts = {"Progressive Firearm Class": 3, "Progressive Outfit Class": 3, "Progressive Tools": 3}
    counts[name] = 2
    state = maximum(world, counts=counts)
    assert state.has("Brain Scorcher Disabled", 1)
    check = multi.get_location("Story: Living Legend / Path Pripyat", 1)
    assert not check.can_reach(state) and not multi.can_beat_game(state)
    state.collect(world.create_item(name), True)
    state.sweep_for_advancements()
    assert check.can_reach(state) and multi.can_beat_game(state)


def test_northern_checks_cannot_use_goodwill_to_bypass_shutdown_or_red_forest():
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"])
    world = multi.worlds[1]
    for missing in ({"Zone Key: Agroprom"}, {"Zone Key: Red Forest"}):
        state = maximum(world, missing)
        assert not multi.get_location("Use Firearm Class: Machinegun", 1).can_reach(state)
        assert not multi.get_location("Reach Armour Tier: Exoskeleton / Nosorog", 1).can_reach(
            state
        )
    state = maximum(world)
    assert multi.get_location("Use Firearm Class: Machinegun", 1).can_reach(state)
    assert multi.get_location("Reach Armour Tier: Exoskeleton / Nosorog", 1).can_reach(state)


def test_recipe_permission_cannot_be_placed_behind_artefact_twenty_one():
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"])
    state = maximum(multi.worlds[1], {"Recipe Access: Artefacts"})
    check = multi.get_location("Discovery: 21 Distinct Artefact Types", 1)
    assert not check.can_reach(state)
    state.collect(multi.worlds[1].create_item("Recipe Access: Artefacts"), True)
    state.sweep_for_advancements()
    assert check.can_reach(state)


@pytest.mark.parametrize("seed", range(10))
def test_full_story_fills_under_all_new_requirements_and_paced_steps_finish(seed):
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"], seed=seed)
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()
    report = analyse(multi.worlds[1], True, True)
    assert report["goal_reachable"] and not report["unreachable_checks"]
    assert any(row.item.name.startswith("Artefact:") for row in multi.get_locations() if row.item)
