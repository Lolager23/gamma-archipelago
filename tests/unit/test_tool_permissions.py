from collections import Counter

import pytest

from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
from gamma_archipelago.content_progression import configured_item_ids, required_copy, tool_level
from gamma_archipelago.tool_permissions import (
    TOOL_CAPABILITIES,
    TOOL_ITEM_IDS,
    TOOL_ITEMS,
    enabled,
    melter_item,
    required_tier,
)


def configuration(**options):
    return build_configuration(
        defaults() | {"equipment_class_progression": 0, "progressive_tool_receipts": 0} | options
    )


def test_new_contract_selects_new_ids_and_keeps_old_seed_manifests_and_wire_unchanged():
    fresh = configuration(rewards_progressive_tools=1, rewards_artefact_melter=1)
    assert enabled(fresh)
    ids = configured_item_ids(fresh)
    assert {28051831, 28051832, 28051833, 28051836} <= ids
    assert not ids & {28051801, 28051802, 28051202, 28051203, 28051204}
    legacy = configuration(
        tool_use_permissions=0, rewards_progressive_tools=1, rewards_artefact_melter=1
    )
    assert not enabled(legacy) and not configured_item_ids(legacy) & TOOL_ITEM_IDS
    assert {28051202, 28051203, 28051204, 28051802} <= configured_item_ids(legacy)
    omitted = legacy.to_values()
    for name in ("tool_use_permissions", "rewards_drug_making_tools", "rewards_gunsmithing_tools"):
        omitted.pop(name)
        assert "option|" + name + "|" not in encode_configuration("a" * 64, legacy, True)
    assert build_configuration(omitted).digest == legacy.digest


def test_contiguous_capabilities_do_not_follow_physical_item_names():
    count = Counter({TOOL_ITEMS["expert"]: 1, TOOL_CAPABILITIES[2]: 1})
    assert tool_level(count.__getitem__) == 0
    count[TOOL_CAPABILITIES[0]] = 1
    assert tool_level(count.__getitem__) == 1
    count[TOOL_CAPABILITIES[1]] = 1
    assert tool_level(count.__getitem__) == 3


@pytest.mark.parametrize("grade,tier", [("A", 0), ("B", 1), ("C", 2), ("D", 3), ("", 0)])
def test_repair_grade_tool_requirement_is_optional_and_matches_native_crafting(grade, tier):
    row = {"weapon_grade": grade}
    assert required_tier(configuration(rewards_progressive_tools=1), row) == tier
    assert required_tier(configuration(rewards_progressive_tools=0), row) == 0
    assert (
        required_tier(configuration(rewards_progressive_tools=1, tool_use_permissions=0), row) == 0
    )
    assert required_tier(configuration(content_progression=0), row) == 0


def test_melter_name_and_mandatory_free_kit_permissions_follow_the_contract():
    assert melter_item(configuration()) == TOOL_ITEMS["artefact"]
    assert melter_item(configuration(tool_use_permissions=0)) == "Artefact Melter"
    for key in TOOL_ITEMS:
        row = {"tool_key": key}
        assert required_copy(configuration(), row) == 1
        assert required_copy(configuration(tool_use_permissions=0), row) == 0
    assert required_copy(configuration(), {"name": "Artefact Melter"}) == 0
    assert (
        required_copy(configuration(), {"name": "Progression Stash: Basic Tools", "tool_level": 1})
        == 0
    )
