"""Named, deterministic starting points; every option remains independently editable."""

from .configuration import (
    CHECK_OPTIONS,
    GEAR_OPTIONS,
    REWARD_OPTIONS,
    build_configuration,
    defaults,
)


def presets() -> dict[str, dict[str, object]]:
    pilot = {**defaults(), "goal": 6}
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
        "progressive_sphere_pacing": 1,
    }
    definitions = {
        "pilot": pilot,
        "explorer": explorer,
        "mvp": mvp,
        "living_legend": {
            **full,
            "goal": 4,
            "checks_mortal_sin": 0,
            "checks_operation_afterglow": 0,
        },
        "full_story": {**full, "goal": 8},
        "full_labs": {**full, "goal": 5},
        "restricted": {
            **mvp,
            "no_starting_weapons": 1,
            "starting_ammo": 0,
            "starting_medicine": 50,
            "starting_money": 25,
        },
        "short": {
            **explorer,
            "opening_policy": 1,
            "generation_preview": 1,
            "starting_pda": 2,
            "rewards_starting_gear_unlocks": 1,
            "rewards_supply_medical": 1,
            "checks_mutant_first_kills": 1,
            "mutant_discovery_mode": 1,
            "mutant_discovery_count": 10,
            "checks_side_task_milestones": 1,
            "grind_profile": 1,
        },
        "standard": {
            **mvp,
            "starting_detector": 0,
            "checks_settlements": 1,
            "opening_policy": 1,
            "generation_preview": 1,
            "access_pacing": 1,
            "rewards_zone_keys": 1,
            "rewards_progressive_tools": 1,
            "rewards_workshop_access": 1,
            "rewards_supply_medical": 1,
            "rewards_supply_maintenance": 1,
            "checks_mutant_first_kills": 1,
            "mutant_discovery_mode": 1,
            "mutant_discovery_count": 15,
            "checks_artefacts": 1,
            "artefact_discovery_mode": 1,
            "artefact_discovery_count": 15,
            "checks_side_task_milestones": 1,
            "grind_profile": 2,
            "combat_logic": 1,
            "progressive_sphere_pacing": 1,
        },
        "extended": {
            **mvp,
            "rewards_drug_making_tools": 1,
            "rewards_gunsmithing_tools": 1,
            "rewards_artefact_melter": 1,
            "starting_detector": 0,
            "goal": 4,
            "checks_settlements": 1,
            "opening_policy": 1,
            "generation_preview": 1,
            "access_pacing": 1,
            "rewards_zone_keys": 1,
            "rewards_quest_keys": 1,
            "rewards_progressive_tools": 1,
            "rewards_workshop_access": 1,
            "rewards_recipe_access": 1,
            "permission_supplies": 1,
            "rewards_supply_medical": 1,
            "rewards_supply_maintenance": 1,
            "rewards_supply_expedition": 1,
            "checks_mutant_first_kills": 1,
            "mutant_discovery_mode": 1,
            "mutant_discovery_count": 20,
            "checks_artefacts": 1,
            "artefact_discovery_mode": 1,
            "artefact_discovery_count": 30,
            "checks_side_task_milestones": 1,
            "checks_story_milestones": 1,
            "grind_profile": 3,
            "combat_logic": 2,
            "progressive_sphere_pacing": 1,
        },
    }

    return {
        name: build_configuration({**values, "ap_start": 1}).to_values()
        for name, values in definitions.items()
    }
