"""Combined systems: generation reachability, not native encounter availability."""

from itertools import product

import pytest
from test_generation_matrix import assert_seed

from gamma_archipelago.presets import presets


@pytest.mark.generation
def test_combined_optional_systems_fill_with_each_scout_policy_and_supply_calibre():
    base = {
        **presets()["extended"],
        "rewards_convenience": 1,
        "rewards_supply_ammunition": 1,
        "checks_shops": 1,
        "checks_faction_standing": 1,
        "checks_gear_upgrades": 1,
        "checks_kill_milestones": 1,
        "discovery_exclusions": ["mutant:bibliotekar", "artefact:af_compass"],
    }
    cases = [
        dict(
            scouting_mode=scout,
            reward_previews=preview,
            optional_check_policy=policy,
            mutant_discovery_mode=quota,
        )
        for scout, preview, policy, quota in product(range(3), range(2), range(3), range(2))
    ] + [
        dict(supply_ammo_calibre=calibre, permission_supplies=supplies, rewards_convenience=carry)
        for calibre, supplies, carry in product(range(5), range(2), range(2))
    ]
    for case in cases:
        for seed in range(3):
            assert_seed({**base, **case}, seed)
