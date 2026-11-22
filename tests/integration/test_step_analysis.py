from collections import Counter

import pytest
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld
from worlds.gamma.analysis import CHAINS, analyse

from gamma_archipelago.presets import presets


@pytest.mark.parametrize("seed", range(10))
def test_paced_analysis_advances_one_tier_per_chain_and_preserves_completion(seed):
    multiworld = setup_multiworld(GammaWorld, options=presets()["full_story"], seed=seed)
    distribute_items_restrictive(multiworld)
    world = multiworld.worlds[1]
    logical = analyse(world, False, True)
    paced = analyse(world, True, True)
    assert logical["goal_reachable"] and paced["goal_reachable"]
    assert logical["unreachable_checks"] == paced["unreachable_checks"] == 0
    assert len(paced["steps"]) >= len(logical["steps"])
    for step in paced["steps"]:
        chains = Counter(
            CHAINS[row["location"]] for row in step["available_checks"] if row["location"] in CHAINS
        )
        assert all(count <= 1 for count in chains.values())
        assert len([name for name in step["local_events"] if name.startswith("Claimed ")]) <= 1
    assert sum(step["checks"] for step in paced["steps"]) == len(
        world.fill_slot_data()["location_ids"]
    )
    summary = analyse(world, True, False)
    assert all("available_checks" not in step for step in summary["steps"])


def test_analysis_reports_unreachable_goal_without_claiming_native_success():
    multiworld = setup_multiworld(GammaWorld, seed=2)
    distribute_items_restrictive(multiworld)
    world = multiworld.worlds[1]
    multiworld.completion_condition[1] = lambda state: state.has("Unobtainable goal", 1)
    for row in multiworld.get_locations():
        row.access_rule = lambda state: False
    report = analyse(world, True, True)
    assert not report["goal_reachable"] and report["goal_step"] is None
    assert report["unreachable_checks"] == 33 and report["steps"] == []


def test_nonfiller_overflow_is_resolved_before_regions_and_fills_all_checks():
    from gamma_archipelago.configuration import build_configuration
    from gamma_archipelago.discovery import configured_location_ids
    from gamma_archipelago.pool_budget import budget_pool
    from gamma_archipelago.reward_quantities import useful_count

    values = presets()["full_story"]
    config = build_configuration(values)
    plan = budget_pool(config, configured_location_ids(config))
    extras = plan.eligible_checks - len(plan.required) - useful_count(Counter(plan.convenience)) + 5
    for seed in range(10):
        multiworld = setup_multiworld(
            GammaWorld, options=values | {"medical_packages": 4 + extras}, seed=seed
        )
        world = multiworld.worlds[1]
        assert world.configuration.option("artefact_overflow_count") == 5
        distribute_items_restrictive(multiworld)
        assert multiworld.can_beat_game()
        assert sum(map(len, multiworld.get_spheres())) == len(multiworld.get_locations())
        assert len(world.fill_slot_data()["location_ids"]) == plan.network_checks + 5


def test_mixed_game_analysis_collects_other_players_rewards_without_pacing_their_chains():
    from worlds.apquest.world import APQuestWorld

    multiworld = setup_multiworld([GammaWorld, APQuestWorld], seed=42)
    distribute_items_restrictive(multiworld)
    report = analyse(multiworld.worlds[1], True, True)
    assert report["goal_reachable"] and report["unreachable_checks"] == 0
    assert sum(step["checks"] for step in report["steps"]) == 33
