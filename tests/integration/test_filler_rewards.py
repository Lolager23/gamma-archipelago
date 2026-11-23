from collections import Counter
from random import Random

from BaseClasses import ItemClassification
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.filler_rewards import candidates
from gamma_archipelago.presets import presets


def test_explicit_reward_mode_randomizes_spare_slots_and_keeps_progression_budget_intact():
    values = presets()["living_legend"]
    multi = setup_multiworld(GammaWorld, options=values, seed=907)
    world = multi.worlds[1]
    pool = Counter(item.name for item in multi.itempool)
    pool.update(
        location.item.name
        for location in multi.get_locations(1)
        if location.address is not None and location.item is not None
    )
    budget = world.pool_budget
    assert all(pool[name] >= count for name, count in Counter(budget.required).items())
    assert pool["Medical Supply Package"] == values["medical_packages"]
    assert not pool["Bandage"] and not pool["Medkit"]
    selected = {name for name, _ in candidates(world.configuration)} & pool.keys()
    assert len(selected) >= 5
    assert all(
        world.create_item(name).classification == ItemClassification.filler for name in selected
    )
    assert sum(pool.values()) == budget.network_checks
    world.random = Random(900)
    first = [world.get_filler_item_name() for _ in range(30)]
    world.random = Random(900)
    assert first == [world.get_filler_item_name() for _ in range(30)]
    assert len(set(first)) >= 5


def test_upstream_filler_replacement_uses_enabled_categories_and_legacy_keeps_bandage():
    values = {"rewards_supply_ammunition": 1}
    world = setup_multiworld(GammaWorld, options=values, seed=908).worlds[1]
    assert all("Ammunition" in world.get_filler_item_name() for _ in range(30))
    legacy = setup_multiworld(GammaWorld, options={"varied_filler": 0}, seed=909).worlds[1]
    assert legacy.get_filler_item_name() == "Bandage"
