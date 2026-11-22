import pytest
from BaseClasses import CollectionState
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.presets import presets
from gamma_archipelago.tool_permissions import TOOL_CAPABILITIES, TOOL_ITEMS, TOOL_TIERS


def settings(**options):
    return presets()["full_story"] | options


def test_class_c_cannot_hold_its_advanced_tool_permission_behind_itself():
    multi = setup_multiworld(GammaWorld, options=settings())
    world = multi.worlds[1]
    state = CollectionState(multi)
    for item in multi.itempool + [row.item for row in multi.get_filled_locations()]:
        if item.name not in {*TOOL_TIERS[1:], *TOOL_CAPABILITIES}:
            state.collect(item, True)
    state.sweep_for_advancements()
    check = multi.get_location("Use Firearm Repair Class: C", 1)
    assert state.has(TOOL_CAPABILITIES[0], 1)
    assert not check.can_reach(state)
    state.collect(world.create_item(TOOL_ITEMS["advanced"]), True)
    state.sweep_for_advancements()
    assert check.can_reach(state)


def test_direct_kit_permissions_do_not_require_a_cordon_stash_visit():
    multi = setup_multiworld(GammaWorld, options=settings(starting_location=2))
    world = multi.worlds[1]
    state = CollectionState(multi)
    for name in TOOL_TIERS:
        state.collect(world.create_item(name), True)
    state.sweep_for_advancements()
    assert not state.can_reach_region("l01_escape", 1)
    assert all(state.has(name, 1) for name in TOOL_CAPABILITIES)
    assert not any(loc.name.startswith("Claimed ") for loc in multi.get_locations())


def test_tool_check_requirements_follow_category_and_contract_toggles():
    for options in (
        settings(rewards_progressive_tools=0),
        settings(tool_use_permissions=0),
        settings(content_progression=0),
    ):
        multi = setup_multiworld(GammaWorld, options=options)
        state = CollectionState(multi)
        for item in multi.itempool + [loc.item for loc in multi.get_filled_locations()]:
            if item.name not in {*TOOL_TIERS, *TOOL_CAPABILITIES}:
                state.collect(item, True)
        state.sweep_for_advancements()
        if options["content_progression"]:
            assert multi.get_location("Use Firearm Repair Class: C", 1).can_reach(state)
        else:
            assert not any(
                loc.name == "Use Firearm Repair Class: C" for loc in multi.get_locations()
            )


def test_new_permissions_keep_advanced_and_expert_placement_pacing():
    multi = setup_multiworld(GammaWorld, options=settings())
    world = multi.worlds[1]
    cordon = multi.get_location("Cordon: First Arrival", 1)
    rostok = multi.get_location("Rostok: First Arrival", 1)
    north = multi.get_location("Jupiter: First Arrival", 1)
    assert cordon.item_rule(world.create_item(TOOL_ITEMS["basic"]))
    assert not cordon.item_rule(world.create_item(TOOL_ITEMS["advanced"]))
    assert rostok.item_rule(world.create_item(TOOL_ITEMS["advanced"]))
    assert not rostok.item_rule(world.create_item(TOOL_ITEMS["expert"]))
    assert north.item_rule(world.create_item(TOOL_ITEMS["expert"]))


def test_map_access_does_not_scan_unrelated_tool_receipts(monkeypatch):
    from worlds.gamma import rules

    multi = setup_multiworld(GammaWorld, options=settings())

    def unexpected_lookup(_count):
        raise AssertionError("Map access should not evaluate tool tiers")

    monkeypatch.setattr(rules, "tool_level", unexpected_lookup)
    assert multi.get_location("Cordon: First Arrival", 1).can_reach(CollectionState(multi))


def test_new_melter_permission_is_independent_of_general_repair_equipment_permission():
    multi = setup_multiworld(GammaWorld, options=settings())
    world = multi.worlds[1]
    state = CollectionState(multi)
    for item in multi.itempool + [loc.item for loc in multi.get_filled_locations()]:
        if item.name not in {TOOL_ITEMS["artefact"], "Equipment Unlock: Tools"}:
            state.collect(item, True)
    state.sweep_for_advancements()
    check = multi.get_location("Discovery: 21 Distinct Artefact Types", 1)
    assert not check.can_reach(state)
    state.collect(world.create_item(TOOL_ITEMS["artefact"]), True)
    state.sweep_for_advancements()
    assert check.can_reach(state)


def test_each_specialist_toggle_adds_exactly_one_permission_without_replacing_recipe_access():
    multi = setup_multiworld(GammaWorld, options=settings())
    items = multi.itempool + [loc.item for loc in multi.get_filled_locations()]
    for name in TOOL_ITEMS.values():
        assert sum(item.name == name for item in items) == 1
    assert any(item.name == "Recipe Access: Ammunition" for item in items)
    off = setup_multiworld(
        GammaWorld,
        options=settings(rewards_drug_making_tools=0, rewards_gunsmithing_tools=0),
    )
    assert not any(
        item.name in {TOOL_ITEMS["medical"], TOOL_ITEMS["ammo"]}
        for item in off.itempool + [loc.item for loc in off.get_filled_locations()]
    )


@pytest.mark.parametrize("seed", range(10))
def test_tool_permissions_fill_without_self_locks_and_paced_analysis_keeps_one_tier(seed):
    from worlds.gamma.analysis import analyse

    multi = setup_multiworld(GammaWorld, options=settings(), seed=seed)
    distribute_items_restrictive(multi)
    assert multi.can_beat_game()
    report = analyse(multi.worlds[1], True, True)
    assert report["goal_reachable"] and report["unreachable_checks"] == 0
    for step in report["steps"]:
        assert len(set(step["local_events"]) & set(TOOL_CAPABILITIES)) <= 1
