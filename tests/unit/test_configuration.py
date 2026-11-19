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


@pytest.mark.parametrize(
    "name",
    tuple(
        name
        for name in CHECK_OPTIONS
        if name
        not in {
            "checks_maps",
            "checks_settlements",
            "checks_mutant_first_kills",
            "checks_faction_first_kills",
            "checks_kill_milestones",
            "checks_artefacts",
            "checks_quest_types",
            "checks_story_milestones",
            "checks_side_task_milestones",
            "checks_gear_upgrades",
            "checks_armour_tiers",
            "checks_weapon_tiers",
            "checks_knife_tiers",
            "checks_rank_milestones",
        }
    )
    + tuple(
        name
        for name in REWARD_OPTIONS
        if name
        not in {
            "rewards_loot_stashes",
            "rewards_progression_stashes",
            "rewards_faction_reputation",
            "rewards_stat_levels",
            "rewards_quest_keys",
        }
    ),
)
def test_unimplemented_adapters_are_never_silently_enabled(name):
    values = defaults()
    values[name] = 1
    with pytest.raises(ConfigurationError, match="Not implemented"):
        build_configuration(values)


@pytest.mark.parametrize("goal", range(1, len(GOALS)))
def test_unimplemented_goals_do_not_fall_back_to_the_pilot(goal):
    with pytest.raises(ConfigurationError, match="Not implemented"):
        build_configuration({**defaults(), "goal": goal})


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
    with pytest.raises(ConfigurationError, match="Not implemented"):
        build_configuration({**defaults(), "starting_pda": 2, "rewards_starting_gear_unlocks": 1})


def test_permission_locks_wait_for_the_permission_adapter_even_with_a_reward_pool(monkeypatch):
    from gamma_archipelago import configuration

    monkeypatch.setattr(
        configuration, "SUPPORTED_REWARDS", frozenset({"rewards_starting_gear_unlocks"})
    )
    with pytest.raises(ConfigurationError, match="Restricted"):
        build_configuration({**defaults(), "starting_pda": 2, "rewards_starting_gear_unlocks": 1})


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
