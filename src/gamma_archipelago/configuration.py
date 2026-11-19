"""Validated, deterministic generation settings shared by APWorld and client."""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass

from .protocol import validate_session_key

CHECK_OPTIONS = (
    "checks_maps",
    "checks_settlements",
    "checks_mutant_first_kills",
    "checks_faction_first_kills",
    "checks_artefacts",
    "checks_quest_types",
    "checks_gear_upgrades",
    "checks_armour_tiers",
    "checks_weapon_tiers",
    "checks_knife_tiers",
    "checks_kill_milestones",
    "checks_side_task_milestones",
    "checks_story_milestones",
    "checks_rank_milestones",
)
REWARD_OPTIONS = (
    "rewards_loot_stashes",
    "rewards_progression_stashes",
    "rewards_quest_keys",
    "rewards_faction_reputation",
    "rewards_stat_levels",
    "rewards_zone_keys",
    "rewards_starting_gear_unlocks",
)
GEAR_OPTIONS = tuple(
    f"starting_{name}"
    for name in (
        "detector",
        "pda",
        "firearms",
        "melee",
        "outfit",
        "helmet",
        "backpack",
        "tools",
        "utilities",
    )
)
QUANTITY_OPTIONS = tuple(f"starting_{name}" for name in ("ammo", "medicine", "food", "money"))
GOALS = (
    "pilot_tour",
    "psi_protection",
    "brain_scorcher",
    "meet_strelok",
    "living_legend",
    "all_x_labs",
)
OPTION_NAMES = (
    CHECK_OPTIONS
    + REWARD_OPTIONS
    + GEAR_OPTIONS
    + QUANTITY_OPTIONS
    + (
        "goal",
        "no_starting_weapons",
        "kill_milestones",
        "side_task_milestones",
    )
)
SUPPORTED_CHECKS = frozenset(
    {
        "checks_maps",
        "checks_settlements",
        "checks_mutant_first_kills",
        "checks_faction_first_kills",
        "checks_kill_milestones",
        "checks_artefacts",
    }
)
SUPPORTED_REWARDS: frozenset[str] = frozenset()
SUPPORTED_GOALS = frozenset({"pilot_tour"})
SUPPORTED_START_MODES = frozenset({0, 1})


class ConfigurationError(ValueError):
    """The selected seed settings are malformed, unsupported or impossible."""


def defaults() -> dict[str, object]:
    values: dict[str, object] = dict.fromkeys(OPTION_NAMES, 0)
    values.update(dict.fromkeys(QUANTITY_OPTIONS, 100))
    values.update(
        checks_maps=1, kill_milestones=[10, 25, 50, 100], side_task_milestones=[5, 10, 20, 40]
    )
    return values


def _integer(values: Mapping[str, object], name: str, maximum: int) -> int:
    value = values[name]
    if type(value) is not int or not 0 <= value <= maximum:
        raise ConfigurationError(f"{name} must be an integer from 0 to {maximum}")
    return value


def _thresholds(value: object) -> tuple[int, ...]:
    if not isinstance(value, list) or not 1 <= len(value) <= 20:
        raise ConfigurationError("Milestones must be a list containing 1 to 20 thresholds")
    if any(type(number) is not int or not 1 <= number <= 10000 for number in value):
        raise ConfigurationError("Milestone thresholds must be integers from 1 to 10000")
    result = tuple(value)
    if result != tuple(sorted(set(result))):
        raise ConfigurationError("Milestone thresholds must be strictly increasing and unique")
    return result


@dataclass(frozen=True)
class SeedConfiguration:
    checks: frozenset[str]
    rewards: frozenset[str]
    goal: str
    gear: tuple[tuple[str, int], ...]
    quantities: tuple[tuple[str, int], ...]
    no_starting_weapons: int
    kill_milestones: tuple[int, ...]
    side_task_milestones: tuple[int, ...]

    def to_values(self) -> dict[str, object]:
        return {
            **{name: int(name in self.checks) for name in CHECK_OPTIONS},
            **{name: int(name in self.rewards) for name in REWARD_OPTIONS},
            **dict(self.gear),
            **dict(self.quantities),
            "goal": GOALS.index(self.goal),
            "no_starting_weapons": self.no_starting_weapons,
            "kill_milestones": list(self.kill_milestones),
            "side_task_milestones": list(self.side_task_milestones),
        }

    @property
    def digest(self) -> str:
        encoded = json.dumps(self.to_values(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def build_configuration(values: Mapping[str, object]) -> SeedConfiguration:
    if set(values) != set(OPTION_NAMES):
        raise ConfigurationError("Configuration must contain exactly the documented option names")
    checks = frozenset(name for name in CHECK_OPTIONS if _integer(values, name, 1))
    rewards = frozenset(name for name in REWARD_OPTIONS if _integer(values, name, 1))
    if not checks:
        raise ConfigurationError("Enable at least one check category")
    goal = GOALS[_integer(values, "goal", len(GOALS) - 1)]
    gear = {name: _integer(values, name, 2) for name in GEAR_OPTIONS}
    no_weapons = _integer(values, "no_starting_weapons", 1)
    if no_weapons:
        for name in ("starting_firearms", "starting_melee"):
            gear[name] = max(1, gear[name])
    if 2 in gear.values() and "rewards_starting_gear_unlocks" not in rewards:
        raise ConfigurationError("AP-locked starts require rewards_starting_gear_unlocks")
    quantities = tuple((name, _integer(values, name, 100)) for name in QUANTITY_OPTIONS)
    unavailable = (checks - SUPPORTED_CHECKS) | (rewards - SUPPORTED_REWARDS)
    if unavailable or goal not in SUPPORTED_GOALS:
        raise ConfigurationError(
            f"Not implemented in this build: {sorted(unavailable)}; goal={goal}"
        )
    if any(mode not in SUPPORTED_START_MODES for mode in gear.values()):
        raise ConfigurationError("Restricted starting loadouts are not implemented in this build")
    return SeedConfiguration(
        checks,
        rewards,
        goal,
        tuple(gear.items()),
        quantities,
        no_weapons,
        _thresholds(values["kill_milestones"]),
        _thresholds(values["side_task_milestones"]),
    )


def encode_configuration(
    session_key: str, configuration: SeedConfiguration, expanded: bool = False
) -> str:
    validate_session_key(session_key)
    lines = [
        f"GAMMA_AP_CONFIG|{2 if expanded else 1}",
        f"session|{session_key}",
        f"digest|{configuration.digest}",
    ]
    for name, value in sorted(configuration.to_values().items()):
        if isinstance(value, list):
            lines.extend(f"threshold|{name}|{number}" for number in value)
        else:
            lines.append(f"option|{name}|{value}")
    lines.append(f"end|{len(lines) - 3}")
    return "\n".join(lines) + "\n"
