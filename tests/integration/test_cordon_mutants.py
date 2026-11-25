from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld
from worlds.gamma.analysis import analyse

from gamma_archipelago.presets import presets


def test_actual_ap_initial_access_and_first_step_include_only_three_mutant_discoveries():
    multi = setup_multiworld(GammaWorld, options=presets()["living_legend"], seed=9303)
    state = CollectionState(multi)
    locations = [
        multi.get_location(f"Discovery: {n} Distinct Mutant Types", 1) for n in range(1, 6)
    ]
    assert [row.can_reach(state) for row in locations] == [True, True, True, False, False]
    state.collect(multi.worlds[1].create_item("Zone Key: Darkscape"), True)
    assert all(row.can_reach(state) for row in locations)
    distribute_items_restrictive(multi)
    for paced in (False, True):
        report = analyse(multi.worlds[1], paced, True)
        initial = {row["location"] for row in report["steps"][0]["available_checks"]}
        assert initial.intersection(row.name for row in locations) == {
            row.name for row in locations[:3]
        }
        assert report["goal_reachable"] and report["unreachable_checks"] == 0
