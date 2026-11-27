from collections import Counter

import pytest

from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
from gamma_archipelago.content_progression import configured_item_ids, required_copy
from gamma_archipelago.equipment_classes import (
    GROUPS,
    armour_check_allowed,
    baseline_rewards,
    check_classes,
    count_with_aliases,
    enabled,
    level,
)
from gamma_archipelago.starting_unlock import unlock_candidates


def configuration(**options):
    return build_configuration(defaults() | {"rewards_starting_gear_unlocks": 1} | options)


@pytest.mark.parametrize("group", GROUPS)
def test_starting_class_is_one_and_receipts_unlock_cumulatively_without_reusing_old_ids(group):
    row = GROUPS[group]
    config = configuration()
    count = Counter()
    assert level(config, group, count.__getitem__) == 1
    assert not baseline_rewards(config)
    assert required_copy(config, {"class_group": group}) == len(row["labels"]) - 1
    for expected in range(2, len(row["labels"]) + 1):
        count[row["item_name"]] += 1
        assert level(config, group, count.__getitem__) == expected
    count[row["item_name"]] += 5
    assert level(config, group, count.__getitem__) == len(row["labels"])
    zero = configuration(**{row["option"]: 0})
    assert level(zero, group, Counter().__getitem__) == 0
    assert row["item_name"] in baseline_rewards(zero)
    assert count_with_aliases(zero, Counter().__getitem__)(row["legacy"]) == 0
    assert count_with_aliases(config, Counter().__getitem__)(row["legacy"]) == 1


def test_fresh_manifest_retires_generic_permissions_but_legacy_wire_and_unlocks_survive():
    config = configuration()
    ids = configured_item_ids(config)
    assert {row["item_id"] for row in GROUPS.values()} <= ids
    assert not ids & {28051603, 28051604, 28051605, 28051606, 28051607, 28051609}
    count = count_with_aliases(config, Counter({"other": 2}).__getitem__)
    assert count("Equipment Unlock: Melee") == count("Equipment Unlock: Tools") == 1
    assert count("other") == 2
    legacy = configuration(equipment_class_progression=0, starting_firearms=2)
    assert not enabled(legacy) and not baseline_rewards(legacy)
    assert level(legacy, "firearms", Counter().__getitem__) == 0
    assert level(legacy, "firearms", Counter({"Equipment Unlock: Firearms": 1}).__getitem__) == 4
    assert level(legacy, "outfit", Counter().__getitem__) == 5
    assert count_with_aliases(legacy, Counter().__getitem__)("Equipment Unlock: Melee") == 0
    assert check_classes(legacy, {}) == {}
    values = legacy.to_values()
    values.pop("equipment_class_progression")
    assert build_configuration(values).digest == legacy.digest
    assert "option|equipment_class_progression" not in encode_configuration("a" * 64, legacy)


def test_class_requirements_follow_each_tier():
    config = configuration(rewards_progressive_tools=1)
    assert check_classes(config, {"category": "checks_armour_tiers", "key": "4"}) == {}
    assert check_classes(config, {"category": "checks_weapon_tiers", "key": "rifle"}) == {
        "firearms": 3
    }
    assert check_classes(config, {"category": "checks_weapon_tiers", "weapon_grade": "D"}) == {
        "firearms": 4
    }
    assert check_classes(config, {"category": "checks_maps"}) == {}


def test_random_start_only_offers_equipment_that_is_actually_locked():
    config = configuration(starting_pda=2, starting_detector=2, random_starting_unlock=1)
    assert unlock_candidates(config, {}) == ("Equipment Unlock: PDA", "Equipment Unlock: Detector")
    zero = configuration(initial_firearm_class=0)
    assert unlock_candidates(zero, {}) == ("Progressive Firearm Class",)
    assert not unlock_candidates(zero, {"Progressive Firearm Class": 1})


def test_generic_tool_receipts_replace_named_tiers_and_always_require_three_copies():
    config = configuration(rewards_progressive_tools=1)
    ids = configured_item_ids(config)
    assert 28051801 in ids and not ids & {28051831, 28051832, 28051833}
    assert required_copy(config, {"name": "Progressive Tools"}) == 3


@pytest.mark.parametrize("tier", [1, 2, 3, 4])
@pytest.mark.parametrize("route", ["outfit", "helmet", "neither"])
def test_armour_checks_accept_either_matching_class_without_the_other_chain(tier, route):
    outfit = tier + 1 if route == "outfit" else tier
    helmet = tier if route == "helmet" else tier - 1
    config = configuration(initial_outfit_class=outfit, initial_helmet_class=helmet)
    row = {"category": "checks_armour_tiers", "key": str(tier)}
    assert armour_check_allowed(config, row, Counter().__getitem__) == (route != "neither")
    assert armour_check_allowed(config, {"category": "checks_weapon_tiers"}, Counter().__getitem__)


def test_legacy_armour_check_uses_either_binary_permission_and_keeps_configuration_identity():
    config = configuration(equipment_class_progression=0, starting_outfit=2, starting_helmet=2)
    row = {"category": "checks_armour_tiers", "key": "3"}
    assert not armour_check_allowed(config, row, Counter().__getitem__)
    for name in ("Equipment Unlock: Outfit", "Equipment Unlock: Helmet"):
        assert armour_check_allowed(config, row, Counter({name: 1}).__getitem__)
    values = config.to_values()
    assert build_configuration(values).digest == config.digest
