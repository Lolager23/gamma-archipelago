from collections import Counter

import pytest

from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.playability import (
    allowed,
    early_check,
    firearm_required,
    fragile_ids,
    goodwill_required,
    late_equipment,
    protected,
)


def config(**values):
    return build_configuration(defaults() | values)


@pytest.mark.parametrize(
    "category,minimum,expected",
    [
        ("checks_kill_milestones", 25, False),
        ("checks_kill_milestones", 26, True),
        ("checks_mutant_first_kills", 5, False),
        ("checks_mutant_first_kills", 6, True),
        ("checks_faction_first_kills", 1, True),
        ("checks_artefacts", 40, False),
    ],
)
def test_knife_ceiling_is_a_capability_requirement(category, minimum, expected):
    row = dict(category=category, minimum=minimum)
    assert firearm_required(row) == expected
    assert not firearm_required(dict(category="checks_mutant_first_kills", key="boar"))
    assert firearm_required(dict(category="checks_mutant_first_kills", key="controller"))
    values = config(starting_firearms=2, rewards_starting_gear_unlocks=1)
    assert allowed(values, row, Counter().__getitem__, lambda _: True) != expected
    assert allowed(
        values, row, Counter({"Equipment Unlock: Firearms": 1}).__getitem__, lambda _: True
    )
    assert allowed(config(playability_logic=0), row, lambda _: 0, lambda _: False)


def test_ap_goodwill_proxy_requires_one_faction_not_combined_native_reputation():
    row = dict(category="checks_rank_milestones", minimum=49999)
    values = config(rewards_faction_reputation=1)
    held = Counter({"Faction Goodwill: stalker": 6, "Faction Goodwill: ecolog": 6})
    assert goodwill_required(row) == 3000
    assert not allowed(values, row, held.__getitem__, lambda _: True)
    held["Faction Goodwill: stalker"] = 12
    assert allowed(values, row, held.__getitem__, lambda _: True)
    assert goodwill_required(dict(category="checks_faction_standing", minimum=2000)) == 2000
    assert protected(config())
    assert protected(values) == protected(config(playability_logic=0))
    assert 28052921 not in fragile_ids(values)
    assert 28052921 in fragile_ids(config(playability_logic=0))


@pytest.mark.parametrize("playability", [0, 1])
@pytest.mark.parametrize("reputation", [0, 1])
def test_every_rank_is_filler_only_regardless_of_goodwill_or_legacy_logic(playability, reputation):
    values = config(playability_logic=playability, rewards_faction_reputation=reputation)
    ranks = frozenset(range(28052801, 28052809))
    assert ranks <= protected(values)
    # Unsupported faction-standing checks keep their existing protection.
    assert (len(protected(values)) > len(ranks)) == bool(playability and not reputation)


def test_heavy_equipment_has_two_independent_access_routes():
    row = dict(category="checks_armour_tiers", key="3")
    values = config(rewards_faction_reputation=1)
    assert late_equipment(row)
    assert late_equipment(dict(category="checks_weapon_tiers", weapon_grade="D"))
    assert not late_equipment(dict(category="checks_armour_tiers", key="2"))
    assert not allowed(values, row, lambda _: 0, lambda _: True)
    assert allowed(
        values,
        row,
        Counter({"Calibrated Psi Protection": 1}).__getitem__,
        {"l10_red_forest", "jupiter"}.__contains__,
    )
    assert not allowed(
        values,
        row,
        Counter({"Calibrated Psi Protection": 1}).__getitem__,
        {"l10_red_forest"}.__contains__,
    )
    assert allowed(
        values, row, Counter({"Faction Goodwill: stalker": 8}).__getitem__, lambda _: False
    )


@pytest.mark.parametrize(
    "row,expected",
    [
        ({"level": "l01_escape", "price": 2500}, True),
        ({"level": "l01_escape", "price": 15000}, False),
        ({"level": "pripyat"}, False),
        ({"level": "Menu", "category": "checks_gear_upgrades"}, False),
        ({"level": "Menu", "category": "checks_artefacts", "minimum": 15}, False),
        ({"level": "Menu", "category": "checks_artefacts", "minimum": 5}, True),
        (
            {
                "level": "Menu",
                "category": "checks_quest_types",
                "logic": {"all_regions": ["pripyat"]},
            },
            False,
        ),
        (
            {
                "level": "Menu",
                "category": "checks_quest_types",
                "logic": {"any_regions": ["pripyat"]},
            },
            False,
        ),
        (
            {
                "level": "Menu",
                "category": "checks_quest_types",
                "logic": {"any_regions": ["l01_escape"]},
            },
            True,
        ),
    ],
)
def test_early_equipment_locations_reject_deep_grind_and_expensive_contracts(row, expected):
    row = {"category": "checks_maps", **row}
    assert early_check(row, frozenset({"l01_escape"})) == expected
