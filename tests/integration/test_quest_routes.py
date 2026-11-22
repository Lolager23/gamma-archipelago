import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from Options import OptionError
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.presets import presets


def maximum_except(multi, missing):
    state = CollectionState(multi)
    network = [loc.item for loc in multi.get_filled_locations(1) if loc.address is not None]
    for item in [*multi.itempool, *network]:
        if item.name not in missing:
            state.collect(item, True)
    state.sweep_for_advancements()
    return state


def test_new_04_agroprom_at_generators_cannot_bootstrap_its_own_quest_route():
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"], seed=14124683978877828916)
    state = maximum_except(multi, {"Zone Key: Agroprom"})
    generators = multi.get_location("Generators: First Arrival", 1)
    assert not state.can_reach_region("l03_agroprom", 1)
    assert not state.has("Brain Scorcher Disabled", 1)
    assert not generators.can_reach(state)
    state.collect(multi.worlds[1].create_item("Zone Key: Agroprom"), True)
    state.sweep_for_advancements()
    assert state.has("Brain Scorcher Disabled", 1)
    assert state.has("Miracle Machine Disabled", 1)
    assert generators.can_reach(state)
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()


@pytest.mark.parametrize("goal", range(9))
def test_shutdown_events_exist_for_every_goal_and_do_not_consume_network_checks(goal):
    multi = setup_multiworld(GammaWorld, options={"goal": goal})
    events = {loc.item.name for loc in multi.get_filled_locations(1) if loc.address is None}
    assert {"Miracle Machine Disabled", "Brain Scorcher Disabled"} <= events
    assert len([loc for loc in multi.get_locations(1) if loc.address is not None]) == 33
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()


def test_sparse_exploration_uses_the_same_story_gates_as_general_fill():
    multi = setup_multiworld(GammaWorld, options={"rewards_zone_keys": 1}, seed=42)
    distribute_items_restrictive(multi)
    state = CollectionState(multi)
    state.sweep_for_advancements()
    assert all(loc.can_reach(state) for loc in multi.get_locations())


def test_quest_permission_cannot_be_placed_beyond_its_shutdown_dependency():
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"])
    state = maximum_except(multi, {"Quest Key: Living Legend"})
    assert not state.has("Brain Scorcher Disabled", 1)
    assert not state.can_reach_region("l13_generators", 1)


def test_impossible_locked_pda_map_only_opening_reports_the_missing_slack():
    with pytest.raises(OptionError, match="another reliable check category"):
        setup_multiworld(
            GammaWorld,
            options={
                "starting_pda": 2,
                "rewards_starting_gear_unlocks": 1,
                "rewards_zone_keys": 1,
            },
        )


@pytest.mark.parametrize("gift", ["Equipment Unlock: PDA", "Zone Key: Garbage"])
def test_a_starting_permission_or_reachable_key_provides_the_required_slack(gift):
    from test_pacing import started_world

    multi, world = started_world(
        {"starting_pda": 2, "rewards_starting_gear_unlocks": 1, "rewards_zone_keys": 1},
        (gift,),
    )
    world.pre_fill()
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()
