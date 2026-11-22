"""Explicit labels for bounded APWorld settings in the local workbench."""

from .expansion_settings import EXPANSION_LIMITS
from .reward_quantities import DEFAULT_COUNTS

CHOICES = {
    "reward_quantities": ["Legacy weighted rewards", "Explicit repeatable reward quantities"],
    "content_progression": [
        "Legacy content contracts",
        "Tiered artefacts, tools and split story arcs",
    ],
    "infinite_stamina": ["Normal stamina", "Infinite stamina"],
    "playability_logic": ["Legacy assumptions", "Practical progression and early equipment"],
    "settlement_reputation_logic": [
        "Legacy settlement access",
        "Require neutral hostile settlements",
    ],
    "ap_start": ["Legacy seed", "Archipelago start required"],
    "starting_faction": ["Free Stalkers"],
    "random_starting_unlock": [
        "No random starting permission",
        "One random locked PDA, firearm or detector",
    ],
    "starting_location": [
        "Rookie Village",
        "Clear Sky Base",
        "Rostok lodging house",
        "Random location",
    ],
    "scouting_mode": ["Disabled", "Local rewards", "Shared AP location hints"],
    "reward_previews": ["Hidden", "Show next milestone reward"],
    "mutant_discovery_mode": ["Per type", "First N distinct types"],
    "faction_discovery_mode": ["Per faction", "First N distinct factions"],
    "artefact_discovery_mode": ["Per type", "First N distinct types"],
    "optional_check_policy": [
        "Exclude progression/useful rewards",
        "Omit fragile checks",
        "Allow progression",
    ],
    "permission_supplies": ["Permissions only", "Permission plus supplies"],
    "supply_ammo_calibre": ["9x18", "9x19", "5.45x39", "5.56x45", "7.62x39"],
    "opening_policy": ["Legacy / challenge", "Protect local Cordon opening"],
    "access_pacing": ["Archipelago randomized access", "Prefer an early hub key"],
    "combat_logic": [
        "Any weapon permission",
        "Firearm permission",
        "Firearm, outfit and helmet permissions",
    ],
    "grind_profile": ["Custom thresholds", "Short", "Standard", "Extended"],
    "generation_preview": ["No seed report", "Seed summary", "Seed report with placement spoilers"],
    "pda_tracker": ["Disabled", "PDA tracker enabled"],
}


def advanced_options() -> list[dict[str, object]]:
    return [
        {
            "key": key,
            "label": "PDA tracker" if key == "pda_tracker" else key.replace("_", " ").capitalize(),
            "maximum": maximum,
            "choices": CHOICES.get(key),
        }
        for key, maximum in {"pda_tracker": 1, **EXPANSION_LIMITS}.items()
        if key not in {"ap_start", "artefact_overflow_count", *DEFAULT_COUNTS}
    ]
