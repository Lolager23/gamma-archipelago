from collections import Counter

import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld
from worlds.gamma.analysis import analyse

from gamma_archipelago.equipment_classes import GROUPS
from gamma_archipelago.presets import presets
from gamma_archipelago.tool_permissions import TOOL_CAPABILITIES


@pytest.mark.parametrize("seed", range(10))
def test_class_receipts_and_generic_tools_fill_without_self_locks(seed):
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"], seed=seed)
    world = multi.worlds[1]
    items = multi.itempool + [row.item for row in multi.get_filled_locations()]
    counts = Counter(item.name for item in items)
    for row in GROUPS.values():
        assert counts[row["item_name"]] == len(row["labels"]) - 1
        assert counts[row["legacy"]] == 0
    assert counts["Progressive Tools"] == 3
    assert counts["Equipment Unlock: Melee"] == counts["Equipment Unlock: Tools"] == 0
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()
    report = analyse(world, True, True)
    assert report["goal_reachable"] and report["unreachable_checks"] == 0


def test_class_c_requires_two_receipts_from_level_one_and_advanced_tools():
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"])
    world = multi.worlds[1]
    state = CollectionState(multi)
    omitted = {"Progressive Firearm Class", "Progressive Tools", *TOOL_CAPABILITIES}
    for item in multi.itempool + [row.item for row in multi.get_filled_locations()]:
        if item.name not in omitted:
            state.collect(item, True)
    state.sweep_for_advancements()
    check = multi.get_location("Use Firearm Repair Class: C", 1)
    assert not check.can_reach(state)
    state.collect(world.create_item("Progressive Firearm Class"), True)
    state.collect(world.create_item("Progressive Tools"), True)
    state.sweep_for_advancements()
    assert not check.can_reach(state)
    state.collect(world.create_item("Progressive Firearm Class"), True)
    assert not check.can_reach(state)
    state.collect(world.create_item("Progressive Tools"), True)
    state.sweep_for_advancements()
    assert check.can_reach(state)


def test_zero_start_reserves_baseline_classes_without_forcing_all_higher_classes_early():
    options = presets()["full_story"] | {row["option"]: 0 for row in GROUPS.values()}
    multi = setup_multiworld(GammaWorld, options=options, seed=3)
    world = multi.worlds[1]
    placed = Counter(row["item"] for row in world.opening_placements)
    assert all(placed[row["item_name"]] == 1 for row in GROUPS.values())
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()


def test_step_calculator_applies_only_one_generic_class_and_tool_tier_per_step():
    from worlds.gamma.analysis import _collect

    multi = setup_multiworld(GammaWorld, options=presets()["full_story"])
    world = multi.worlds[1]
    state = CollectionState(multi)
    location = multi.get_location("Cordon: First Arrival", 1)
    pending = [
        (world.create_item(name), location)
        for name in ["Progressive Firearm Class"] * 3 + ["Progressive Tools"] * 3
    ]
    for tier in range(1, 4):
        pending = _collect(state, pending, True)
        assert state.count("Progressive Firearm Class", 1) == tier
        assert state.count("Progressive Tools", 1) == tier
    assert not pending


def test_class_contract_rejects_a_legacy_manifest_even_when_it_looks_plausible():
    import asyncio

    from test_client import connected_context

    from gamma_archipelago.catalog import enabled_item_ids
    from gamma_archipelago.protocol import ProtocolError

    world = setup_multiworld(GammaWorld, options=presets()["full_story"]).worlds[1]
    data = world.fill_slot_data()
    data["item_ids"] = sorted(enabled_item_ids(world.configuration.rewards))

    async def exercise():
        with pytest.raises(ProtocolError, match="manifest"):
            connected_context(data)

    asyncio.run(exercise())
