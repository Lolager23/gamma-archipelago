"""Enemy totals are numeric planning tiers, independent of AP access rules."""

import pytest
from BaseClasses import CollectionState, Location
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld
from worlds.gamma.analysis import _reachable, analyse

from gamma_archipelago.catalog import KILL_MILESTONE_BASE, MAX_KILL_MILESTONE


def options(totals):
    return {
        "checks_maps": 0,
        "checks_kill_milestones": 1,
        "kill_milestones": totals,
        "grind_profile": 0,
    }


@pytest.mark.parametrize("totals", [[10, 25, 50, 100], [3, 7, 11], [1, MAX_KILL_MILESTONE]])
def test_each_configured_enemy_total_takes_a_new_paced_step(totals):
    multi = setup_multiworld(GammaWorld, options=options(totals), seed=35)
    distribute_items_restrictive(multi)
    world = multi.worlds[1]
    logical = analyse(world, False, True)
    paced = analyse(world, True, True)
    names = [multi.get_location(f"Defeat {total} Enemies", 1).name for total in totals]
    assert [row["location"] for row in logical["steps"][0]["available_checks"]] == names
    assert [[row["location"] for row in wave["available_checks"]] for wave in paced["steps"]] == [
        [name] for name in names
    ]
    assert logical["goal_reachable"] and paced["goal_reachable"]
    assert logical["unreachable_checks"] == paced["unreachable_checks"] == 0


def test_two_gamma_players_have_independent_enemy_chains():
    multi = setup_multiworld([GammaWorld, GammaWorld], options=options([10, 25]), seed=3)
    distribute_items_restrictive(multi)
    state = CollectionState(multi)
    state.sweep_for_advancements(
        locations=[row for row in multi.get_locations() if row.address is None]
    )
    remaining = set(multi.get_filled_locations())
    first = _reachable(multi.worlds[1], state, remaining, True)
    kills = [
        row for row in first if row.address in {KILL_MILESTONE_BASE + 10, KILL_MILESTONE_BASE + 25}
    ]
    assert {(row.player, row.address) for row in kills} == {
        (player, KILL_MILESTONE_BASE + 10) for player in (1, 2)
    }


def test_other_games_are_not_paced_even_when_their_names_and_ids_match():
    from worlds.apquest.world import APQuestWorld

    multi = setup_multiworld([GammaWorld, APQuestWorld], seed=42)
    parent = multi.get_region(multi.worlds[2].origin_region_name, 2)
    rows = {
        Location(2, f"Defeat {total} Enemies", KILL_MILESTONE_BASE + total, parent)
        for total in (10, 25)
    }
    assert set(_reachable(multi.worlds[1], CollectionState(multi), rows, True)) == rows


def test_an_unreachable_lower_enemy_total_cannot_be_skipped_by_the_paced_plan():
    multi = setup_multiworld(GammaWorld, options=options([10, 25]), seed=3)
    distribute_items_restrictive(multi)
    first = multi.get_location("Defeat 10 Enemies", 1)
    second = multi.get_location("Defeat 25 Enemies", 1)
    first.access_rule = lambda state: False
    state = CollectionState(multi)
    assert _reachable(multi.worlds[1], state, {first, second}, False) == [second]
    assert _reachable(multi.worlds[1], state, {first, second}, True) == []
