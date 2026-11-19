"""Additional bounded settings; legacy values preserve pre-expansion seed identities."""

EXPANSION_LIMITS = {"scouting_mode": 2, "reward_previews": 1}
EXPANSION_DEFAULTS = dict.fromkeys(EXPANSION_LIMITS, 0)
LEGACY_CHECK_DEFAULTS = {"checks_shops": 0, "checks_faction_standing": 0}
