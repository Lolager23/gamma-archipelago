import pytest

from gamma_archipelago.configuration import (
    CHECK_OPTIONS,
    GEAR_OPTIONS,
    GOALS,
    OPTION_NAMES,
    QUANTITY_OPTIONS,
    REWARD_OPTIONS,
    ConfigurationError,
    build_configuration,
    defaults,
    encode_configuration,
)
from gamma_archipelago.protocol import ProtocolError
from gamma_archipelago.session import SessionCoordinator


def test_tracker_defaults_preserve_legacy_digest_and_nondefault_choice_is_bound():
    values = defaults()
    legacy = {key: value for key, value in values.items() if key != "pda_tracker"}
    assert build_configuration(legacy).digest == build_configuration(values).digest
    assert (
        build_configuration({**values, "pda_tracker": 0}).digest
        != build_configuration(values).digest
    )
    for invalid in (True, -1, 2, "1"):
        with pytest.raises(ConfigurationError, match="pda_tracker"):
            build_configuration({**values, "pda_tracker": invalid})


def test_default_configuration_is_immutable_and_deterministically_serialized():
    values = defaults()
    configuration = build_configuration(values)
    assert configuration.checks == {"checks_maps"} and not configuration.rewards
    assert configuration.goal == "pilot_tour"
    assert configuration.kill_milestones == (10, 25, 50, 100)
    assert set(values) == set(OPTION_NAMES)
    assert configuration.to_values() == values
    assert build_configuration(configuration.to_values()).digest == configuration.digest
    values["kill_milestones"].append(200)
    assert configuration.kill_milestones == (10, 25, 50, 100)
    assert len(configuration.digest) == 64


def test_all_requested_check_reward_and_goal_adapters_are_available():
    from gamma_archipelago.configuration import SUPPORTED_CHECKS, SUPPORTED_GOALS, SUPPORTED_REWARDS

    assert set(CHECK_OPTIONS) == SUPPORTED_CHECKS
    assert set(REWARD_OPTIONS) == SUPPORTED_REWARDS
    assert set(GOALS) == SUPPORTED_GOALS


@pytest.mark.parametrize(
    "change",
    [
        {"extra": 0},
        {"checks_maps": 0},
        {"checks_maps": True},
        {"checks_maps": -1},
        {"rewards_zone_keys": 2},
        {"goal": 6},
        {"no_starting_weapons": 2},
        {"starting_pda": 3},
        {"starting_money": 101},
    ],
)
def test_configuration_names_values_and_empty_pools_are_validated(change):
    with pytest.raises(ConfigurationError):
        build_configuration({**defaults(), **change})
    values = defaults()
    values.pop("goal")
    with pytest.raises(ConfigurationError):
        build_configuration(values)


@pytest.mark.parametrize("name", GEAR_OPTIONS + QUANTITY_OPTIONS + ("no_starting_weapons",))
def test_initial_omission_and_quantity_options_are_supported(name):
    configuration = build_configuration({**defaults(), name: 1})
    assert configuration.to_values()[name] == 1


def test_ap_locked_equipment_requires_its_unlock_reward_pool():
    with pytest.raises(ConfigurationError, match="require rewards_starting_gear_unlocks"):
        build_configuration({**defaults(), "starting_pda": 2, "no_starting_weapons": 1})
    assert (
        dict(
            build_configuration(
                {**defaults(), "starting_pda": 2, "rewards_starting_gear_unlocks": 1}
            ).gear
        )["starting_pda"]
        == 2
    )


def test_unlock_rewards_require_a_selected_locked_start():
    with pytest.raises(ConfigurationError, match="at least one AP-locked"):
        build_configuration({**defaults(), "rewards_starting_gear_unlocks": 1})


@pytest.mark.parametrize("thresholds", [None, [], [1] * 21, [True], [0], [10001], [2, 1], [1, 1]])
def test_milestones_are_bounded_finite_and_strictly_increasing(thresholds):
    with pytest.raises(ConfigurationError, match="[Mm]ilestone"):
        build_configuration({**defaults(), "kill_milestones": thresholds})


def test_session_configuration_cannot_change_without_changing_the_session():
    session = SessionCoordinator("a" * 64)
    session.bind_configuration(None)
    session.bind_configuration(None)
    with pytest.raises(ProtocolError, match="changed"):
        session.bind_configuration("b" * 64)
    configured = SessionCoordinator("a" * 64)
    configured.bind_configuration("b" * 64)
    with pytest.raises(ProtocolError):
        configured.bind_configuration("invalid")


def test_wire_configuration_is_deterministic_and_item_v2_references_its_identity(tmp_path):
    from gamma_archipelago.bridge import FileBridge
    from gamma_archipelago.protocol import encode_incoming

    configuration = build_configuration({**defaults(), "no_starting_weapons": 1})
    assert dict(configuration.gear)["starting_firearms"] == 1
    assert dict(configuration.gear)["starting_melee"] == 1
    expected = encode_configuration("a" * 64, configuration)
    bridge = FileBridge(tmp_path, allowed_root=tmp_path)
    bridge.write_configuration("a" * 64, configuration)
    bridge.write_history("a" * 64, (), configuration.digest)
    assert (bridge.directory / "configuration.txt").read_text() == expected
    assert expected.startswith(
        f"GAMMA_AP_CONFIG|1\nsession|{'a' * 64}\ndigest|{configuration.digest}\n"
    )
    assert (bridge.directory / "incoming.txt").read_text().startswith("GAMMA_AP_IN|2\n")
    with pytest.raises(ProtocolError):
        encode_incoming("a" * 64, (), "bad")


def test_quest_key_seed_requires_checks_outside_the_locked_story():
    with pytest.raises(ConfigurationError, match="outside"):
        build_configuration(
            {**defaults(), "checks_maps": 0, "checks_story_milestones": 1, "rewards_quest_keys": 1}
        )


def test_travel_configuration_preserves_old_default_digest_and_requires_zone_keys():
    import hashlib
    import json

    values = defaults()
    values.pop("zone_unlock_travel")
    values.pop("pda_tracker")
    from gamma_archipelago.expansion_settings import EXPANSION_DEFAULTS, LEGACY_REWARD_DEFAULTS

    values.pop("discovery_exclusions")
    for name in EXPANSION_DEFAULTS:
        values.pop(name)
    for name in LEGACY_REWARD_DEFAULTS:
        values.pop(name)
    for name in ("checks_shops", "checks_faction_standing"):
        values.pop(name)
    expected = hashlib.sha256(
        json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert build_configuration(values).digest == expected
    with pytest.raises(ConfigurationError, match="requires zone keys"):
        build_configuration({**defaults(), "zone_unlock_travel": 1})
    enabled = build_configuration({**defaults(), "rewards_zone_keys": 1, "zone_unlock_travel": 1})
    assert enabled.zone_unlock_travel == 1 and enabled.digest != expected


def test_exclusive_psi_stash_and_zone_chain_need_early_unreserved_check_slots():
    with pytest.raises(ConfigurationError, match="require settlement checks"):
        build_configuration(
            {**defaults(), "rewards_zone_keys": 1, "rewards_progression_stashes": 1}
        )
