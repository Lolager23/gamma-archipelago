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
    multiworld = setup_multiworld(GammaWorld, seed=22, options={option: 1, "reward_quantities": 0})
    distribute_items_restrictive(multiworld)
    names = [row.item.name for row in multiworld.get_locations(1)]
    assert sum("Supply Package" in name for name in names) > 0
    assert "Basic Toolkit" in names
    result = preview({**defaults(), option: 1}, {})
    assert result["required_rewards"] == 0
    supplies = [row for row in result["rewards"] if row.get("effect") == "supply_package"]
    assert len([row for row in supplies if row["classification"] == "useful"]) == 1
    assert all(row["category"] == option for row in supplies)
    assert any(row.get("filler_family") == category for row in supplies)
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
    } | {"reward_quantities": 0}
    for seed in range(50):
        assert_seed(options, seed)
        assert_seed(
            {**options, "checks_maps": 0, "checks_kill_milestones": 1, "kill_milestones": [1]}, seed
        )


def test_legacy_optional_pool_does_not_put_a_useful_toolkit_in_excluded_shops():
    multiworld = setup_multiworld(
        GammaWorld, options={"checks_maps": 0, "checks_shops": 1, "reward_quantities": 0}
    )
    distribute_items_restrictive(multiworld)
    locations = [loc for loc in multiworld.get_locations(1) if loc.address is not None]
    assert len(locations) == 3
    assert all(
        row.item.name != "Basic Toolkit" and not row.item.advancement and not row.item.useful
        for row in locations
    )
