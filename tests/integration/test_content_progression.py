import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.presets import presets


def test_tiered_tool_pool_and_placement_requirements_are_explicit():
    multi = setup_multiworld(
        GammaWorld, options=presets()["full_story"] | {"tool_use_permissions": 0}
    )
    world = multi.worlds[1]
    assert not any(item.name == "Progressive Tools" for item in multi.itempool)
    names = {item.name for item in multi.itempool}
    assert {
        "Progression Stash: Basic Tools",
        "Progression Stash: Advanced Tools",
        "Progression Stash: Expert Tools",
        "Artefact Melter",
    } <= names
    cordon = next(loc for loc in multi.get_locations() if loc.address == 28052001)
    north = multi.get_location("Jupiter: First Arrival", 1)
    assert not cordon.item_rule(world.create_item("Progression Stash: Expert Tools"))
    assert north.item_rule(world.create_item("Progression Stash: Expert Tools"))
    assert multi.get_location("Rostok: First Arrival", 1).item_rule(
        world.create_item("Progression Stash: Advanced Tools")
    )


def test_artefact_twenty_one_requires_the_melter_and_its_use_permission():
    options = presets()["full_story"] | {"tool_use_permissions": 0}
    multi = setup_multiworld(GammaWorld, options=options)
    world = multi.worlds[1]
    state = CollectionState(multi)
    for item in multi.itempool + [row.item for row in multi.get_filled_locations()]:
        if item.name not in {"Artefact Melter", "Equipment Unlock: Tools"}:
            state.collect(item, True)
    check = multi.get_location("Discovery: 21 Distinct Artefact Types", 1)
    assert not check.can_reach(state)
    state.collect(world.create_item("Artefact Melter"), True)
    assert not check.can_reach(state)
    state.collect(world.create_item("Equipment Unlock: Tools"), True)
    assert check.can_reach(state)


@pytest.mark.generation
@pytest.mark.parametrize("goal", [4, 7, 8])
def test_content_and_new_story_goals_fill_and_reach_every_check(goal):
    for seed in range(10):
        multi = setup_multiworld(
            GammaWorld, options=presets()["full_story"] | {"goal": goal}, seed=seed
        )
        distribute_items_restrictive(multi)
        assert multi.can_beat_game()
        assert sum(map(len, multi.get_spheres())) == len(multi.get_locations())


def test_rostock_start_needs_a_route_to_claim_the_cordon_tool_kits():
    multi = setup_multiworld(
        GammaWorld,
        options=presets()["full_story"] | {"starting_location": 2, "tool_use_permissions": 0},
    )
    world = multi.worlds[1]
    state = CollectionState(multi)
    for name in (
        "Progression Stash: Basic Tools",
        "Progression Stash: Advanced Tools",
        "Progression Stash: Expert Tools",
        "Equipment Unlock: Tools",
        "Workshop Access: Upgrades",
    ):
        state.collect(world.create_item(name), True)
    state.sweep_for_advancements()
    assert not state.can_reach_region("l01_escape", 1)
    assert not multi.get_location("Install 1 Firearm Upgrades", 1).can_reach(state)
    state.collect(world.create_item("Zone Key: Garbage"), True)
    state.sweep_for_advancements()
    assert state.can_reach_region("l01_escape", 1)
    assert multi.get_location("Install 1 Firearm Upgrades", 1).can_reach(state)


@pytest.mark.generation
@pytest.mark.parametrize("starting", [1, 2, 3])
def test_tool_claim_routes_fill_from_every_supported_start(starting):
    for seed in range(10):
        multi = setup_multiworld(
            GammaWorld,
            options=presets()["full_story"]
            | {"starting_location": starting, "tool_use_permissions": 0},
            seed=seed,
        )
        distribute_items_restrictive(multi)
        assert multi.can_beat_game()


@pytest.mark.parametrize("goal", [4, 5])
def test_constrained_tool_stash_regression_seed_260_fills_without_swapping_dead_ends(goal):
    multi = setup_multiworld(
        GammaWorld,
        options=presets()["full_story"] | {"goal": goal, "tool_use_permissions": 0},
        seed=260,
    )
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()
    assert sum(map(len, multi.get_spheres())) == len(multi.get_locations())
