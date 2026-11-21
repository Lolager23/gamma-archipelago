import pytest
from BaseClasses import CollectionState
from Options import OptionError
from test.general import setup_multiworld
from test_generation_matrix import assert_seed
from worlds.gamma import GammaWorld

from gamma_archipelago.catalog import LOCATION_CATEGORIES
from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.web_planner import preview


def test_three_tool_copies_precede_filler_and_solver_requires_expert_for_upgrade_checks():
    multiworld = setup_multiworld(
        GammaWorld, seed=9, options=dict(rewards_progressive_tools=1, checks_gear_upgrades=1)
    )
    world = multiworld.worlds[1]
    assert sum(item.name == "Progressive Tools" for item in multiworld.itempool) == 3
    state = CollectionState(multiworld)
    upgrades = [
        row
        for row in multiworld.get_locations(1)
        if LOCATION_CATEGORIES.get(row.address) == "checks_gear_upgrades"
    ]
    assert upgrades
    for _ in range(3):
        assert not any(row.can_reach(state) for row in upgrades)
        state.collect(world.create_item("Progressive Tools"))
    assert all(row.can_reach(state) for row in upgrades)
    values = {**defaults(), "ap_start": 1, "rewards_progressive_tools": 1}
    assert preview(values, {})["required_rewards"] == 3
    legacy = defaults()
    legacy.pop("rewards_progressive_tools")
    assert build_configuration(legacy).digest == build_configuration(defaults()).digest
    with pytest.raises(OptionError, match="cannot hold"):
        setup_multiworld(
            GammaWorld,
            options={
                **values,
                "checks_maps": 0,
                "checks_side_task_milestones": 1,
                "side_task_milestones": [1],
            },
        )


@pytest.mark.generation
def test_progressive_tools_fill_without_placing_permissions_behind_their_checks():
    for seed in range(50):
        assert_seed(dict(rewards_progressive_tools=1, checks_gear_upgrades=1), seed)
