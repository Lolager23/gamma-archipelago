"""Found, bought or starting equipment does not need repair to earn a use check."""

import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld
from worlds.gamma import GammaWorld

from gamma_archipelago.content_progression import TOOL_CLAIMS
from gamma_archipelago.presets import presets
from gamma_archipelago.tool_permissions import TOOL_CAPABILITIES, TOOL_TIERS


@pytest.mark.parametrize("classes", [0, 1])
@pytest.mark.parametrize("permissions", [0, 1])
@pytest.mark.parametrize("generic", [0, 1])
def test_all_equipment_use_checks_are_in_logic_without_tools(classes, permissions, generic):
    options = presets()["living_legend"] | dict(
        equipment_class_progression=classes,
        tool_use_permissions=permissions,
        progressive_tool_receipts=generic,
        regional_progression=0,
        playability_logic=0,
        quest_zone_logic=0,
    )
    multi = setup_multiworld(GammaWorld, options=options)
    state = CollectionState(multi)
    excluded = {*TOOL_CAPABILITIES, *TOOL_TIERS, *TOOL_CLAIMS, "Progressive Tools"}
    excluded.update(f"Progression Stash: {tier} Tools" for tier in ("Basic", "Advanced", "Expert"))
    for item in multi.itempool + [row.item for row in multi.get_filled_locations()]:
        if item.name not in excluded:
            state.collect(item, True)
    state.sweep_for_advancements()
    assert not any(state.count(name, 1) for name in excluded)
    for location in multi.get_locations():
        if location.name.startswith(("Use Firearm ", "Reach Armour Tier:", "Reach Knife Tier ")):
            assert location.can_reach(state), location.name
    # Installation actions still need tools and workshop access.
    assert not multi.get_location("Install 1 Firearm Upgrades", 1).can_reach(state)


def test_starting_pistol_smg_and_purchased_knives_are_open_before_first_tool_reward():
    multi = setup_multiworld(GammaWorld, options=presets()["living_legend"])
    state = CollectionState(multi)
    names = ("Use Firearm Class: Pistol", "Use Firearm Class: Smg", "Use Firearm Repair Class: A")
    for name in names:
        assert multi.get_location(name, 1).can_reach(state)
    knives = [
        location
        for location in multi.get_locations()
        if location.name.startswith("Reach Knife Tier ")
    ]
    assert len(knives) == 4
    assert all(location.can_reach(state) for location in knives)
    assert not state.has("Progressive Tools", 1)
