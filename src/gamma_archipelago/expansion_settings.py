"""Additional bounded settings; legacy values preserve pre-expansion seed identities."""

EXPANSION_LIMITS = {
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
    "rewards_progressive_tools": 0,
    "rewards_workshop_access": 0,
    "rewards_recipe_access": 0,
}
LEGACY_CHECK_DEFAULTS = {"checks_shops": 0, "checks_faction_standing": 0}
