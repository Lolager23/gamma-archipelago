"""Additional bounded settings; legacy values preserve pre-expansion seed identities."""

EXPANSION_LIMITS = {
    "ap_start": 1,
    "starting_faction": 0,
    "starting_location": 3,
    "opening_policy": 1,
    "access_pacing": 1,
    "combat_logic": 2,
    "grind_profile": 3,
    "generation_preview": 2,
    "supply_ammo_calibre": 4,
    "permission_supplies": 1,
    "scouting_mode": 2,
    "reward_previews": 1,
    "mutant_discovery_mode": 1,
    "mutant_discovery_count": 25,
    "faction_discovery_mode": 1,
    "faction_discovery_count": 13,
    "artefact_discovery_mode": 1,
    "artefact_discovery_count": 66,
    "optional_check_policy": 2,
}
EXPANSION_DEFAULTS = dict.fromkeys(EXPANSION_LIMITS, 0)
LEGACY_REWARD_DEFAULTS = {
    "rewards_convenience": 0,
    "rewards_supply_medical": 0,
    "rewards_supply_maintenance": 0,
    "rewards_supply_ammunition": 0,
    "rewards_supply_expedition": 0,
    "rewards_progressive_tools": 0,
    "rewards_workshop_access": 0,
    "rewards_recipe_access": 0,
}
LEGACY_CHECK_DEFAULTS = {
    "checks_shops": 0,
    "checks_shop_purchases": 0,
    "checks_faction_standing": 0,
}
