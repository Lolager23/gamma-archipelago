"""Story presets stop at the selected arc and preserve the trilogy's key chain."""

import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.presets import presets


@pytest.mark.parametrize("name", ["living_legend", "full_story"])
@pytest.mark.parametrize("seed", [83, 260, 20261122])
def test_each_story_tier_fills_reaches_its_goal_and_has_no_unreachable_checks(name, seed):
    multi = setup_multiworld(GammaWorld, options=presets()[name], seed=seed)
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()
    assert sum(map(len, multi.get_spheres())) == len(multi.get_locations())
    assert multi.worlds[1].fill_slot_data()["goal"] == (
        "living_legend" if name == "living_legend" else "operation_afterglow"
    )


def test_living_legend_needs_no_post_legend_events_or_keys():
    multi = setup_multiworld(GammaWorld, options=presets()["living_legend"])
    names = {location.name for location in multi.get_locations()}
    assert "Return After Living Legend" in names
    assert "Return After Mortal Sin" not in names
    assert "Finish Operation Afterglow" not in names
    assert not any(
        name.startswith(("Story: Mortal Sin", "Story: Operation Afterglow")) for name in names
    )
    state = CollectionState(multi)
    assert not multi.completion_condition[1](state)
    state.collect(multi.get_location("Return After Living Legend", 1).item, True)
    assert multi.completion_condition[1](state)


@pytest.mark.parametrize("missing", ["Living Legend", "Mortal Sin", "Operation Afterglow"])
def test_full_story_cannot_finish_without_each_chain_permission(missing):
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"])
    world = multi.worlds[1]
    state = CollectionState(multi)
    for item in multi.itempool + [location.item for location in multi.get_filled_locations()]:
        if item.code is not None and item.name != "Quest Key: " + missing:
            state.collect(item, True)
    state.sweep_for_advancements()
    assert not multi.completion_condition[1](state)
    state.collect(world.create_item("Quest Key: " + missing), True)
    state.sweep_for_advancements()
    assert multi.completion_condition[1](state)


def test_full_story_completion_events_remain_ordered():
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"])
    state = CollectionState(multi)
    for item in multi.itempool + [location.item for location in multi.get_filled_locations()]:
        if item.name not in {
            "Living Legend Complete",
            "Mortal Sin Complete",
            "Operation Afterglow Complete",
        }:
            state.collect(item, True)
    mortal = multi.get_location("Return After Mortal Sin", 1)
    afterglow = multi.get_location("Finish Operation Afterglow", 1)
    assert not mortal.can_reach(state) and not afterglow.can_reach(state)
    state.collect(multi.get_location("Return After Living Legend", 1).item, True)
    assert mortal.can_reach(state) and not afterglow.can_reach(state)
    assert not multi.completion_condition[1](state)
    state.collect(mortal.item, True)
    assert afterglow.can_reach(state) and not multi.completion_condition[1](state)
    state.collect(afterglow.item, True)
    assert multi.completion_condition[1](state)
