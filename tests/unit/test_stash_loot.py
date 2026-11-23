from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration


def test_stash_randomization_defaults_on_but_omitted_legacy_field_retains_digest():
    fresh = build_configuration(defaults())
    assert fresh.option("randomized_stash_loot") == 1
    old = defaults()
    old.pop("randomized_stash_loot")
    legacy = build_configuration(old)
    assert legacy.option("randomized_stash_loot") == 0
    assert legacy.digest == build_configuration(old | {"randomized_stash_loot": 0}).digest
    assert "option|randomized_stash_loot" not in encode_configuration("a" * 64, legacy)
