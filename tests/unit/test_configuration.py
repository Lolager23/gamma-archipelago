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


@pytest.mark.parametrize("name", CHECK_OPTIONS[1:] + REWARD_OPTIONS)
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
def test_restricted_start_modes_wait_for_their_engine_adapter(name):
    with pytest.raises(ConfigurationError, match="Restricted"):
        build_configuration({**defaults(), name: 1})


def test_ap_locked_equipment_requires_its_unlock_reward_pool():
    with pytest.raises(ConfigurationError, match="require rewards_starting_gear_unlocks"):
        build_configuration({**defaults(), "starting_pda": 2, "no_starting_weapons": 1})
    with pytest.raises(ConfigurationError, match="Not implemented"):
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
