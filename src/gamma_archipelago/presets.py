"""Named, deterministic starting points; every option remains independently editable."""

from .configuration import (
    CHECK_OPTIONS,
    GEAR_OPTIONS,
    REWARD_OPTIONS,
    build_configuration,
    defaults,
)


def presets() -> dict[str, dict[str, object]]:
    pilot = defaults()
    explorer = {
        **defaults(),
        "checks_settlements": 1,
        "rewards_loot_stashes": 1,
        "rewards_faction_reputation": 1,
    }
    mvp = {
        **defaults(),
        "goal": 2,
        "starting_pda": 2,
        "starting_detector": 2,
        "rewards_starting_gear_unlocks": 1,
        "rewards_progression_stashes": 1,
        "rewards_loot_stashes": 1,
    }
    full = {
        **defaults(),
        **dict.fromkeys(CHECK_OPTIONS + REWARD_OPTIONS, 1),
        **dict.fromkeys(GEAR_OPTIONS, 2),
        "zone_unlock_travel": 1,
    }
    definitions = {
        "pilot": pilot,
        "explorer": explorer,
        "mvp": mvp,
        "full_story": {**full, "goal": 4},
        "full_labs": {**full, "goal": 5},
        "restricted": {
            **mvp,
            "no_starting_weapons": 1,
            "starting_ammo": 0,
            "starting_medicine": 50,
            "starting_money": 25,
        },
    }

    return {name: build_configuration(values).to_values() for name, values in definitions.items()}
