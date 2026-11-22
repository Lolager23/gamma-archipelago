from collections import Counter

import pytest

from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
from gamma_archipelago.quest_routes import NORTHERN_ZONES, SHUTDOWNS, allowed


@pytest.mark.parametrize("held", [(), SHUTDOWNS[:1], SHUTDOWNS[1:], SHUTDOWNS])
def test_north_requires_both_native_shutdowns_not_just_one(held):
    configuration = build_configuration(defaults())
    counts = Counter(held)
    assert allowed(configuration, "l13_generators", counts.__getitem__) == (held == SHUTDOWNS)
    assert allowed(configuration, "l10_radar", counts.__getitem__)
    assert allowed(configuration, "l08u_brainlab", counts.__getitem__)
    assert "l10_red_forest" in NORTHERN_ZONES


def test_omitted_contract_retains_old_seed_identity_and_wire_format():
    values = defaults()
    values.pop("quest_zone_logic")
    old = build_configuration(values)
    explicit = build_configuration(values | {"quest_zone_logic": 0})
    assert old.digest == explicit.digest
    assert "quest_zone_logic" not in encode_configuration("a" * 64, old)
    assert allowed(old, "l13_generators", lambda _: 0)
