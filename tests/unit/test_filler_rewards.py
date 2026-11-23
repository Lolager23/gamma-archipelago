import json
from importlib.resources import files

import pytest

from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
from gamma_archipelago.content_progression import configured_item_ids
from gamma_archipelago.filler_rewards import candidates
from gamma_archipelago.presets import presets
from gamma_archipelago.reward_quantities import requested

ROWS = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text())["items"]
NEW = [row for row in ROWS if row.get("filler_family")]


def test_fresh_filler_is_varied_nonprogression_and_only_uses_enabled_categories():
    config = build_configuration(presets()["living_legend"])
    choices = dict(candidates(config))
    assert {row["name"] for row in NEW} <= choices.keys()
    assert not {"Bandage", "Medkit"} & choices.keys()
    assert len(choices) == 35  # Advanced stashes remain useful, outside filler-only checks.
    assert all(weight > 0 for weight in choices.values())
    assert all(row["classification"] == "filler" for row in ROWS if row["name"] in choices)
    assert {row["filler_family"] for row in NEW} == {
        "medical",
        "maintenance",
        "ammunition",
        "expedition",
    }


@pytest.mark.parametrize("family", ["medical", "maintenance", "ammunition", "expedition"])
def test_a_single_enabled_supply_category_cannot_draw_another_family(family):
    config = build_configuration(defaults() | {"rewards_supply_" + family: 1})
    assert {name for name, _ in candidates(config)} == {
        row["name"] for row in NEW if row["filler_family"] == family
    }
    assert all(
        row["id"] in configured_item_ids(config) for row in NEW if row["filler_family"] == family
    )


def test_legacy_mode_preserves_original_manifest_and_disabled_wire_format():
    values = presets()["living_legend"]
    values.pop("varied_filler")
    legacy = build_configuration(values)
    assert candidates(legacy) == (("Bandage", 1),)
    assert not {row["id"] for row in NEW} & configured_item_ids(legacy)
    assert legacy.digest == build_configuration(values | {"varied_filler": 0}).digest
    assert "option|varied_filler" not in encode_configuration("a" * 64, legacy)


def test_disabled_alternatives_use_basic_fallback_and_guaranteed_packages_keep_their_counts():
    assert candidates(build_configuration(defaults())) == (("Medkit", 1), ("Bandage", 1))
    config = build_configuration(defaults() | {"rewards_supply_medical": 1, "medical_packages": 7})
    assert requested(config) == {"Medical Supply Package": 7}
    loot = build_configuration(defaults() | {"rewards_loot_stashes": 1})
    assert all("Loot Stash:" in name for name, _ in candidates(loot))
