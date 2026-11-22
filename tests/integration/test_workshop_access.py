import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld
from test_generation_matrix import assert_seed
from worlds.gamma import GammaWorld

from gamma_archipelago.catalog import LOCATION_CATEGORIES
from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.web_planner import preview


def test_workshop_pool_and_native_upgrade_requirements_are_independent_of_tool_tiers():
    multiworld = setup_multiworld(
        GammaWorld,
        options=dict(rewards_workshop_access=1, rewards_recipe_access=1, checks_gear_upgrades=1),
    )
    names = [item.name for item in multiworld.itempool] + [
        loc.item.name for loc in multiworld.get_filled_locations(1)
    ]
    assert len([name for name in names if name.startswith("Workshop Access:")]) == 3
    assert len([name for name in names if name.startswith("Recipe Access:")]) == 4
    state = CollectionState(multiworld)
    upgrades = [
        row
        for row in multiworld.get_locations(1)
        if LOCATION_CATEGORIES.get(row.address) == "checks_gear_upgrades"
    ]
    assert not any(row.can_reach(state) for row in upgrades)
    state.collect(multiworld.worlds[1].create_item("Workshop Access: Upgrades"))
    assert all(row.can_reach(state) for row in upgrades)
    values = {**defaults(), "rewards_workshop_access": 1, "rewards_recipe_access": 1}
    assert preview(values, {})["required_rewards"] == 7
    legacy = defaults()
    for name in ("rewards_workshop_access", "rewards_recipe_access"):
        legacy.pop(name)
    assert build_configuration(legacy).digest == build_configuration(defaults()).digest


@pytest.mark.generation
def test_all_permission_systems_generate_with_upgrade_checks():
    for seed in range(50):
        assert_seed(
            dict(
                rewards_workshop_access=1,
                rewards_recipe_access=1,
                rewards_progressive_tools=1,
                checks_gear_upgrades=1,
            ),
            seed,
        )
