import pytest
from BaseClasses import CollectionState
from Options import OptionError
from test.general import setup_multiworld
from test_generation_matrix import assert_seed
from worlds.gamma import GammaWorld

from gamma_archipelago.catalog import LOCATION_CATEGORIES
from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.web_planner import preview


@pytest.mark.parametrize("generic", [0, 1])
def test_fresh_upgrade_counts_need_only_basic_permission_with_other_access_satisfied(generic):
    from gamma_archipelago.content_progression import TOOL_CLAIMS
    from gamma_archipelago.presets import presets
    from gamma_archipelago.tool_permissions import TOOL_CAPABILITIES, TOOL_TIERS

    multi = setup_multiworld(
        GammaWorld, options=presets()["living_legend"] | {"progressive_tool_receipts": generic}
    )
    world = multi.worlds[1]
    state = CollectionState(multi)
    excluded = {*TOOL_CAPABILITIES, *TOOL_TIERS, *TOOL_CLAIMS, "Progressive Tools"}
    excluded.update(f"Progression Stash: {tier} Tools" for tier in ("Basic", "Advanced", "Expert"))
    for item in multi.itempool + [row.item for row in multi.get_filled_locations()]:
        if item.name not in excluded:
            state.collect(item, True)
    upgrades = [
        row
        for row in multi.get_locations(1)
        if LOCATION_CATEGORIES.get(row.address) == "checks_gear_upgrades"
    ]
    assert upgrades and not any(row.can_reach(state) for row in upgrades)
    state.collect(
        world.create_item("Progressive Tools" if generic else "Tool Use: Basic Tools"), True
    )
    state.sweep_for_advancements()
    assert all(row.can_reach(state) for row in upgrades)
    assert not state.has("Usable Advanced Tools", 1)
    assert not state.has("Usable Expert Tools", 1)


def test_three_tool_copies_precede_filler_and_solver_requires_basic_for_aggregate_upgrade_checks():
    multiworld = setup_multiworld(
        GammaWorld,
        seed=9,
        options=dict(rewards_progressive_tools=1, checks_gear_upgrades=1, content_progression=0),
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
    assert not any(row.can_reach(state) for row in upgrades)
    for _ in range(3):
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
                "content_progression": 0,
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
