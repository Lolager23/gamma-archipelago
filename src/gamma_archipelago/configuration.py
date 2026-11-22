"""Validated, deterministic generation settings shared by APWorld and client."""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass

from .discovery import configured_location_ids, normalize_exclusions
from .expansion_settings import (
    EXPANSION_DEFAULTS,
    EXPANSION_LIMITS,
    LEGACY_CHECK_DEFAULTS,
    LEGACY_REWARD_DEFAULTS,
)
from .protocol import validate_session_key
from .reward_quantities import DEFAULT_COUNTS

CHECK_OPTIONS = (
    "checks_emissions",
    "checks_psi_storms",
    "checks_mortal_sin",
    "checks_operation_afterglow",
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
    "checks_shops",
    "checks_shop_purchases",
    "checks_faction_standing",
)
REWARD_OPTIONS = (
    "rewards_artefact_melter",
    "rewards_supply_medical",
    "rewards_supply_maintenance",
    "rewards_supply_ammunition",
    "rewards_supply_expedition",
    "rewards_convenience",
    "rewards_workshop_access",
    "rewards_recipe_access",
    "rewards_progressive_tools",
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
    "talk_sidorovich",
    "mortal_sin",
    "operation_afterglow",
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
        "zone_unlock_travel",
        "pda_tracker",
        "discovery_exclusions",
    )
    + tuple(EXPANSION_LIMITS)
)
SUPPORTED_CHECKS = frozenset(
    {
        "checks_emissions",
        "checks_psi_storms",
        "checks_mortal_sin",
        "checks_operation_afterglow",
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
        "checks_shops",
        "checks_shop_purchases",
        "checks_faction_standing",
    }
)
SUPPORTED_REWARDS: frozenset[str] = frozenset(
    {
        "rewards_artefact_melter",
        "rewards_supply_medical",
        "rewards_supply_maintenance",
        "rewards_supply_ammunition",
        "rewards_supply_expedition",
        "rewards_convenience",
        "rewards_workshop_access",
        "rewards_recipe_access",
        "rewards_progressive_tools",
        "rewards_loot_stashes",
        "rewards_progression_stashes",
        "rewards_faction_reputation",
        "rewards_stat_levels",
        "rewards_quest_keys",
        "rewards_starting_gear_unlocks",
        "rewards_zone_keys",
    }
)
SUPPORTED_GOALS = frozenset(
    {
        "pilot_tour",
        "psi_protection",
        "brain_scorcher",
        "meet_strelok",
        "living_legend",
        "all_x_labs",
        "talk_sidorovich",
        "mortal_sin",
        "operation_afterglow",
    }
)


class ConfigurationError(ValueError):
    """The selected seed settings are malformed, unsupported or impossible."""


def defaults() -> dict[str, object]:
    """Defaults for new generation and planner forms; saved settings override them."""
    values: dict[str, object] = dict.fromkeys(OPTION_NAMES, 0)
    values.update(dict.fromkeys(QUANTITY_OPTIONS, 100))
    values.update(
        checks_maps=1,
        pda_tracker=1,
        kill_milestones=[10, 25, 50, 100],
        side_task_milestones=[5, 10, 20, 40],
        discovery_exclusions=[],
        mutant_discovery_mode=1,
        faction_discovery_mode=1,
        artefact_discovery_mode=1,
        settlement_reputation_logic=1,
        playability_logic=1,
        content_progression=1,
        reward_quantities=1,
        artefact_extra_ceiling=60,
        **{name: count for name, count in DEFAULT_COUNTS.items()},
        artefact_discovery_count=40,
    )
    return values


def legacy_defaults() -> dict[str, object]:
    """Compatibility baseline; generation defaults must not redefine older sessions."""
    return {**defaults(), **EXPANSION_DEFAULTS}


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
    zone_unlock_travel: int
    pda_tracker: int = 1
    expansion: tuple[tuple[str, int], ...] = ()
    discovery_exclusions: tuple[str, ...] = ()

    def option(self, name: str) -> int:
        return dict(self.expansion).get(name, EXPANSION_DEFAULTS[name])

    def to_values(self) -> dict[str, object]:
        return {
            **{name: int(name in self.checks) for name in CHECK_OPTIONS},
            **{name: int(name in self.rewards) for name in REWARD_OPTIONS},
            **dict(self.gear),
            **dict(self.quantities),
            **{name: self.option(name) for name in EXPANSION_LIMITS},
            "goal": GOALS.index(self.goal),
            "no_starting_weapons": self.no_starting_weapons,
            "kill_milestones": list(self.kill_milestones),
            "side_task_milestones": list(self.side_task_milestones),
            "zone_unlock_travel": self.zone_unlock_travel,
            "pda_tracker": self.pda_tracker,
            "discovery_exclusions": list(self.discovery_exclusions),
        }

    @property
    def digest(self) -> str:
        values = self.to_values()
        if not self.discovery_exclusions:
            values.pop("discovery_exclusions")
        for name, default in (
            EXPANSION_DEFAULTS | LEGACY_CHECK_DEFAULTS | LEGACY_REWARD_DEFAULTS
        ).items():
            if values[name] == default:
                values.pop(name)
        if self.pda_tracker == 1:
            values.pop("pda_tracker")  # Presentation default preserves existing seed identities.
        if not self.zone_unlock_travel:
            values.pop("zone_unlock_travel")  # Preserve pre-travel configuration identities.
        encoded = json.dumps(values, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def build_configuration(values: Mapping[str, object]) -> SeedConfiguration:
    values = {
        "discovery_exclusions": [],
        **EXPANSION_DEFAULTS,
        **LEGACY_CHECK_DEFAULTS,
        **LEGACY_REWARD_DEFAULTS,
        **values,
    }
    grind = _integer(values, "grind_profile", 3)
    if grind:
        kills, tasks = (
            ((5, 15, 30), (1, 3, 6)),
            ((10, 25, 50, 100), (5, 10, 20, 40)),
            ((25, 75, 150, 250), (10, 25, 50, 75)),
        )[grind - 1]
        values = {**values, "kill_milestones": list(kills), "side_task_milestones": list(tasks)}
    if "pda_tracker" not in values:
        values = {**values, "pda_tracker": 1}
    if "zone_unlock_travel" not in values:
        values = {**values, "zone_unlock_travel": 0}
    if set(values) != set(OPTION_NAMES):
        raise ConfigurationError("Configuration must contain exactly the documented option names")
    checks = frozenset(name for name in CHECK_OPTIONS if _integer(values, name, 1))
    rewards = frozenset(name for name in REWARD_OPTIONS if _integer(values, name, 1))
    if not checks:
        raise ConfigurationError("Enable at least one check category")
    if (
        checks <= {"checks_story_milestones", "checks_mortal_sin", "checks_operation_afterglow"}
        and "rewards_quest_keys" in rewards
    ):
        raise ConfigurationError("Quest keys require checks outside their locked story chains")
    if "rewards_zone_keys" in rewards and "checks_maps" not in checks:
        raise ConfigurationError("Zone keys require map checks for a guaranteed exploration route")
    if {
        "rewards_zone_keys",
        "rewards_progression_stashes",
    } <= rewards and "checks_settlements" not in checks:
        raise ConfigurationError(
            "Exclusive psi stashes with zone keys require settlement checks for early rewards"
        )
    travel = _integer(values, "zone_unlock_travel", 1)
    if travel and "rewards_zone_keys" not in rewards:
        raise ConfigurationError("Unlock travel requires zone keys")
    goal = GOALS[_integer(values, "goal", len(GOALS) - 1)]
    gear = {name: _integer(values, name, 2) for name in GEAR_OPTIONS}
    no_weapons = _integer(values, "no_starting_weapons", 1)
    if no_weapons:
        for name in ("starting_firearms", "starting_melee"):
            gear[name] = max(1, gear[name])
    if 2 in gear.values() and "rewards_starting_gear_unlocks" not in rewards:
        raise ConfigurationError("AP-locked starts require rewards_starting_gear_unlocks")
    if "rewards_starting_gear_unlocks" in rewards and 2 not in gear.values():
        raise ConfigurationError(
            "Starting gear rewards require at least one AP-locked starting group"
        )
    if values["random_starting_unlock"] and not any(
        gear["starting_" + group] == 2 for group in ("pda", "firearms", "detector")
    ):
        raise ConfigurationError(
            "Random starting unlock needs an AP-locked PDA, firearms or detector"
        )
    quantities = tuple((name, _integer(values, name, 100)) for name in QUANTITY_OPTIONS)
    try:
        exclusions = normalize_exclusions(values["discovery_exclusions"])
    except ValueError as error:
        raise ConfigurationError(str(error)) from error
    configuration = SeedConfiguration(
        checks,
        rewards,
        goal,
        tuple(gear.items()),
        quantities,
        no_weapons,
        _thresholds(values["kill_milestones"]),
        _thresholds(values["side_task_milestones"]),
        travel,
        _integer(values, "pda_tracker", 1),
        tuple(
            (name, _integer(values, name, maximum)) for name, maximum in EXPANSION_LIMITS.items()
        ),
        exclusions,
    )
    try:
        configured_location_ids(configuration)
    except ValueError as error:
        raise ConfigurationError(str(error)) from error
    return configuration


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
        if name == "discovery_exclusions":
            lines.extend(f"exclude|{token}" for token in configuration.discovery_exclusions)
        elif isinstance(value, list):
            lines.extend(f"threshold|{name}|{number}" for number in value)
        elif (
            name
            in {
                "checks_shop_purchases",
                "ap_start",
                "starting_faction",
                "starting_location",
                "random_starting_unlock",
                "mutant_filler_tail",
                "artefact_filler_tail",
                "settlement_reputation_logic",
                "playability_logic",
                "content_progression",
                "infinite_stamina",
                "reward_quantities",
                "artefact_extra_ceiling",
                "artefact_overflow_count",
                *DEFAULT_COUNTS,
            }
            and value == 0
        ):
            continue  # Disabled additions retain the previous add-on's wire format.
        else:
            lines.append(f"option|{name}|{value}")
    lines.append(f"end|{len(lines) - 3}")
    return "\n".join(lines) + "\n"
