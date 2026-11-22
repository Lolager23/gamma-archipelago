import asyncio

import pytest
from BaseClasses import LocationProgressType
from test.general import setup_multiworld
from test_client import connected_context
from test_generation_matrix import assert_seed
from worlds.gamma import GammaWorld

from gamma_archipelago.discovery import (
    GROUPS,
    MISSABLE_IDS,
    QUOTAS,
    SOURCES,
    configured_location_ids,
)
from gamma_archipelago.playability import protected as practical_protected
from gamma_archipelago.presets import presets


@pytest.mark.parametrize("group", GROUPS)
def test_omitted_yaml_mode_defaults_to_generic_but_explicit_per_type_still_works(group):
    options = {"checks_maps": 0, GROUPS[group]: 1}
    world = setup_multiworld(GammaWorld, options=options).worlds[1]
    assert world.configuration.option(f"{group}_discovery_mode") == 1
    assert set(world.fill_slot_data()["location_ids"]) == set(QUOTAS[group])
    named = setup_multiworld(GammaWorld, options={**options, f"{group}_discovery_mode": 0}).worlds[
        1
    ]
    assert set(named.fill_slot_data()["location_ids"]) == set(SOURCES[group].values())


@pytest.mark.parametrize("policy", [0, 1, 2])
def test_world_client_manifest_and_optional_policy_match(policy):
    options = dict(
        checks_mutant_first_kills=1,
        mutant_discovery_mode=1,
        mutant_discovery_count=15,
        checks_shops=1,
        checks_faction_standing=1,
        optional_check_policy=policy,
        discovery_exclusions={"mutant:dog"},
    )
    world = setup_multiworld(GammaWorld, seed=55, options=options).worlds[1]
    data = world.fill_slot_data()
    expected = configured_location_ids(world.configuration)

    async def exercise():
        context = connected_context(data)
        assert context.session.allowed_locations == expected == set(data["location_ids"])

    asyncio.run(exercise())
    assert set(QUOTAS["mutant"][:15]) <= expected
    checks = [row for row in world.multiworld.get_locations(1) if row.address in MISSABLE_IDS]
    assert len(checks) == (0 if policy == 1 else 7)
    assert all(
        (row.progress_type == LocationProgressType.EXCLUDED)
        == (policy == 0 or row.address in practical_protected(world.configuration))
        for row in checks
    )


@pytest.mark.generation
@pytest.mark.parametrize("policy", [0, 1, 2])
def test_quota_seed_fill_with_full_progression_and_missable_policies(policy):
    for seed in range(20):
        assert_seed(
            {
                **presets()["full_story"],
                "mutant_discovery_mode": 1,
                "mutant_discovery_count": 15,
                "faction_discovery_mode": 1,
                "faction_discovery_count": 5,
                "artefact_discovery_mode": 1,
                "artefact_discovery_count": 20,
                "optional_check_policy": policy,
                "discovery_exclusions": ["faction:stalker", "mutant:dog"],
            },
            seed,
        )
