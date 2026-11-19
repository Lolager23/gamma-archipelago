import pytest
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from test_generation_matrix import assert_seed
from worlds.gamma import GammaWorld

from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.web_planner import preview


@pytest.mark.parametrize("category", ["medical", "maintenance", "ammunition", "expedition"])
def test_package_options_are_independent_useful_filler_without_progression_budget(category):
    option = f"rewards_supply_{category}"
    multiworld = setup_multiworld(GammaWorld, seed=22, options={option: 1})
    distribute_items_restrictive(multiworld)
    names = [row.item.name for row in multiworld.get_locations(1)]
    assert sum("Supply Package" in name for name in names) > 0
    assert "Basic Toolkit" in names
    result = preview({**defaults(), option: 1}, {})
    assert result["required_rewards"] == 0
    assert len([row for row in result["rewards"] if row.get("effect") == "supply_package"]) == 1
    legacy = defaults()
    for name in list(legacy):
        if name.startswith("rewards_supply_") or name == "supply_ammo_calibre":
            legacy.pop(name)
    assert build_configuration(legacy).digest == build_configuration(defaults()).digest


@pytest.mark.generation
def test_every_package_category_and_minimal_pools_fill_reproducibly():
    options = {
        f"rewards_supply_{category}": 1
        for category in ("medical", "maintenance", "ammunition", "expedition")
    }
    for seed in range(50):
        assert_seed(options, seed)
        assert_seed(
            {**options, "checks_maps": 0, "checks_kill_milestones": 1, "kill_milestones": [1]}, seed
        )
