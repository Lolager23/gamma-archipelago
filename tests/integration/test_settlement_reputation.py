import pytest
from BaseClasses import CollectionState, ItemClassification, LocationProgressType
from Fill import distribute_items_restrictive
from test.general import gen_steps, setup_multiworld
from worlds.AutoWorld import call_all
from worlds.gamma import GammaWorld

from gamma_archipelago.presets import presets


@pytest.mark.parametrize(
    "faction,ids",
    [("army", (28052103, 28052106)), ("bandit", (28052108,)), ("killer", (28052112,))],
)
def test_hostile_bases_require_five_matching_rewards_and_four_is_still_hostile(faction, ids):
    multi = setup_multiworld(GammaWorld, options=presets()["full_story"], seed=10)
    world = multi.worlds[1]
    name = "Faction Goodwill: " + faction
    assert sum(item.name == name for item in multi.itempool) == 5
    state = CollectionState(multi)
    for item in multi.itempool:
        if item.name != name:
            state.collect(item, True)
    checks = {loc.address: loc for loc in multi.get_locations() if loc.address in ids}
    for _ in range(4):
        state.collect(world.create_item(name), True)
    assert all(not loc.can_reach(state) for loc in checks.values())
    state.collect(world.create_item(name), True)
    assert all(loc.can_reach(state) for loc in checks.values())


def test_initial_inventory_goodwill_is_progression_before_world_generation_and_opens_the_base():
    multi = setup_multiworld(
        GammaWorld,
        steps=(),
        options={
            "checks_settlements": 1,
            "rewards_faction_reputation": 1,
            "start_inventory": {"Faction Goodwill: army": 5},
        },
    )
    world = multi.worlds[1]
    assert not hasattr(world, "configuration")
    # Upstream's small setup helper does not run Main's common start-inventory pass.
    for _ in range(5):
        item = world.create_item("Faction Goodwill: army")
        assert item.advancement
        multi.push_precollected(item)
    for step in gen_steps:
        call_all(multi, step)
    state = CollectionState(multi)
    assert state.has("Faction Goodwill: army", 1, 5)
    assert next(loc for loc in multi.get_locations() if loc.address == 28052103).can_reach(state)


@pytest.mark.parametrize("enabled", [0, 1])
def test_no_supported_neutrality_route_is_filler_only_even_when_missable_progression_is_allowed(
    enabled,
):
    values = presets()["full_story"] | {
        "rewards_faction_reputation": enabled,
        "optional_check_policy": 2,
    }
    multi = setup_multiworld(GammaWorld, options=values)
    ids = (
        {28052113, 28052114}
        if enabled
        else {28052103, 28052106, 28052108, 28052112, 28052113, 28052114}
    )
    checks = [loc for loc in multi.get_locations() if loc.address in ids]
    assert all(loc.progress_type == LocationProgressType.EXCLUDED for loc in checks)
    distribute_items_restrictive(multi)
    assert all(loc.item.classification == ItemClassification.filler for loc in checks)


@pytest.mark.generation
def test_reputation_gates_fill_without_self_locks_in_full_and_settlement_only_pools():
    for options in (
        presets()["full_story"],
        {"checks_maps": 0, "checks_settlements": 1, "rewards_faction_reputation": 1},
    ):
        for seed in range(30):
            multi = setup_multiworld(GammaWorld, options=options, seed=seed)
            distribute_items_restrictive(multi)
            assert multi.can_beat_game()
            seen = set()
            for sphere in multi.get_spheres():
                assert sphere
                seen.update(sphere)
            assert len(seen) == len(multi.get_locations())


@pytest.mark.parametrize("early,local,expected", [(0, 0, 5), (0, 3, 2), (5, 0, 5), (0, 5, 0)])
def test_sparse_early_request_preserves_normal_and_local_user_constraints(early, local, expected):
    from worlds.gamma.settlement_fill import request_neutrality_opener

    multi = setup_multiworld(
        GammaWorld,
        steps=("generate_early", "create_regions", "create_items", "set_rules"),
        options={"checks_maps": 0, "checks_settlements": 1, "rewards_faction_reputation": 1},
    )
    name = "Faction Goodwill: army"
    multi.early_items[1][name] = early
    multi.local_early_items[1][name] = local
    request_neutrality_opener(multi.worlds[1])
    assert multi.early_items[1][name] == expected
    assert multi.local_early_items[1][name] == local


def test_a_constrained_sparse_opening_refuses_an_early_quota_it_cannot_hold():
    from Options import OptionError
    from worlds.gamma.settlement_fill import request_neutrality_opener

    from gamma_archipelago.settlement_access import SETTLEMENT_RULES

    multi = setup_multiworld(
        GammaWorld,
        steps=("generate_early", "create_regions", "create_items", "set_rules"),
        options={
            "checks_maps": 0,
            "checks_settlements": 1,
            "rewards_faction_reputation": 1,
            "starting_pda": 2,
            "rewards_starting_gear_unlocks": 1,
        },
    )
    # Exercise the boundary for a future/external access constraint opening safe
    # checks only after a PDA: do not silently overbook initially reachable slots.
    safe = [loc for loc in multi.get_locations() if loc.address not in SETTLEMENT_RULES]
    for loc in safe[4:]:
        loc.access_rule = lambda state: state.has("Equipment Unlock: PDA", 1)
    with pytest.raises(OptionError, match="initially available"):
        request_neutrality_opener(multi.worlds[1])
