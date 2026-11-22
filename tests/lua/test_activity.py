import pytest

from gamma_archipelago.activity_requirements import regional_requirement
from gamma_archipelago.configuration import build_configuration, defaults

from .test_tracker import CATALOG, rows, state_for, view


@pytest.mark.parametrize(
    "regions",
    [
        set(),
        {"l01_escape"},
        {"k00_marsh"},
        {"l08_yantar"},
        {row["id"] for row in CATALOG["levels"]},
    ],
)
@pytest.mark.parametrize("excluded", [[], ["mutant:boar", "artefact:af_medusa"]])
def test_generated_lua_requirements_match_python_for_every_source_quota_and_category(
    lua, regions, excluded
):
    values = {**defaults(), "discovery_exclusions": excluded}
    config = build_configuration(values)
    state = state_for(lua, discovery_exclusions=excluded)
    choices = lua.table_from({level: True for level in regions})
    for row in CATALOG["locations"]:
        definition = lua.globals().gamma_ap_catalog.tracker_checks[row["id"]]
        actual, reliable = lua.globals().gamma_ap_activity.available(
            state, definition, choices, row["id"]
        )
        expected = regional_requirement(row, config)
        assert actual == expected.accessible(regions.__contains__), row["id"]
        assert reliable == expected.reliable, row["id"]


def test_pda_explains_nearby_activity_permissions_and_optional_uncertain_sources(lua):
    state = state_for(
        lua,
        rewards_zone_keys=1,
        checks_mutant_first_kills=1,
        checks_artefacts=1,
        mutant_discovery_mode=0,
        artefact_discovery_mode=0,
        starting_detector=2,
        rewards_starting_gear_unlocks=1,
    )
    checks = {row.id: row for row in rows(view(lua, state))}
    assert checks[28052202].status == "available"
    assert "Equipment permission" in checks[28052445].reason
    state.unlocks.gear_detector = True
    checks = {row.id: row for row in rows(view(lua, state))}
    assert checks[28052445].status == "available"
    assert "Optional check" in checks[28052401].reason


def test_quota_tracker_requires_new_reachable_types_after_early_roster_is_exhausted(lua):
    state = state_for(
        lua,
        checks_mutant_first_kills=1,
        mutant_discovery_mode=1,
        mutant_discovery_count=25,
        rewards_zone_keys=1,
    )
    checks = {row.id: row for row in rows(view(lua, state))}
    assert checks[28140001].status == "available"
    assert "Regional activity" in checks[28140020].reason
    for key in lua.globals().gamma_ap_catalog.zone_keys.values():
        state.unlocks[key] = True
    checks = {row.id: row for row in rows(view(lua, state))}
    assert "Optional check" in checks[28140025].reason


def test_zero_verified_remaining_sources_never_makes_a_quota_progression_safe(lua):
    excluded = [
        "mutant:" + row["key"]
        for row in CATALOG["locations"]
        if row["category"] == "checks_mutant_first_kills"
        and "logic" in row
        and row["logic"]["reliable"]
    ]
    state = state_for(lua, discovery_exclusions=excluded)
    row = lua.globals().gamma_ap_catalog.tracker_checks[28140001]
    assert lua.globals().gamma_ap_activity.available(state, row, lua.table(), 28140001) == (
        True,
        False,
    )


def test_rank_requires_an_earning_path_and_stored_upgrades_require_tool_use(lua):
    state = state_for(
        lua,
        checks_rank_milestones=1,
        checks_gear_upgrades=1,
        starting_pda=2,
        starting_firearms=2,
        starting_melee=2,
        starting_tools=2,
        rewards_starting_gear_unlocks=1,
    )
    checks = {row.id: row for row in rows(view(lua, state))}
    assert checks[28052801].status == "available"
    assert "rank progression" in checks[28052802].reason
    assert "tools" in checks[28052731].reason
    state.unlocks.gear_pda = True
    state.unlocks.gear_tools = True
    checks = {row.id: row for row in rows(view(lua, state))}
    assert checks[28052802].status == checks[28052731].status == "available"
    state.unlocks.gear_pda = False
    state.unlocks.gear_melee = True
    checks = {row.id: row for row in rows(view(lua, state))}
    assert checks[28052802].status == "blocked"
    state.unlocks.gear_firearms = True
    checks = {row.id: row for row in rows(view(lua, state))}
    assert checks[28052802].status == "available"


def test_story_tracker_keeps_transitive_combat_after_introductory_dialogues(lua):
    lua.execute("has_alife_info=function() return true end")
    from gamma_archipelago.presets import presets

    state = state_for(
        lua,
        **(
            presets()["full_story"]
            | {
                "equipment_class_progression": 0,
                "progressive_tool_receipts": 0,
                "starting_melee": 2,
            }
        ),
    )
    for row in CATALOG["items"]:
        if "permission" in row and row["name"] not in {
            "Equipment Unlock: Firearms",
            "Equipment Unlock: Melee",
        }:
            state.unlocks[row["permission"]] = True
    checks = {row.id: row for row in rows(view(lua, state))}
    assert checks[28052601].status == "available"
    for id in (28052606, 28052611, 28052621, 28052622, 28052644):
        assert "firearm or melee" in checks[id].reason
    state.unlocks.gear_melee = True
    checks = {row.id: row for row in rows(view(lua, state))}
    assert all(
        checks[id].status == "available"
        for id in (28052606, 28052611, 28052621, 28052622, 28052644)
    )


@pytest.mark.parametrize(
    "gear,keys,psi",
    [
        ([], [], False),
        (["PDA"], [], False),
        (["Detector", "Melee"], [], False),
        (["PDA", "Firearms", "Detector"], ["Zone Key: Great Swamps"], False),
        (["PDA", "Firearms", "Melee", "Outfit", "Helmet", "Detector"], None, True),
    ],
)
def test_pda_check_availability_matches_actual_ap_access_rules(lua, gear, keys, psi):
    from BaseClasses import CollectionState
    from test.general import setup_multiworld
    from worlds.gamma import GammaWorld

    from gamma_archipelago.presets import presets

    config = presets()["full_story"]
    multi = setup_multiworld(GammaWorld, options=config, seed=123)
    world = multi.worlds[1]
    ap = CollectionState(multi)
    native = state_for(lua, **config)
    names = ["Equipment Unlock: " + name for name in gear]
    names += (
        keys
        if keys is not None
        else [row["name"] for row in CATALOG["items"] if "permission" in row]
    )
    if psi:
        ap.collect(multi.get_location("Claim Cordon Psi Stash", 1).item, True)
    for name in names:
        item = world.create_item(name)
        ap.collect(item, True)
        permission = lua.globals().gamma_ap_catalog.permissions[item.code]
        if permission:
            native.unlocks[permission] = True
    from gamma_archipelago.tool_permissions import TOOL_CAPABILITIES

    ap.sweep_for_advancements(
        locations=[loc for loc in multi.get_locations() if loc.name in TOOL_CAPABILITIES]
    )
    statuses = {
        row.id: row.status
        for row in rows(lua.globals().gamma_ap_tracker.snapshot(native, 0, None, psi))
    }
    for loc in multi.get_locations():
        if loc.address:
            assert (statuses[loc.address] == "available") == loc.can_reach(ap), loc.name
