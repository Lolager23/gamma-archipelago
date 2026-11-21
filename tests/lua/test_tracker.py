import json
from pathlib import Path

import pytest

from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration

from .test_game_adapter import load_game, set_incoming

ROOT = Path(__file__).resolve().parents[2]
CATALOG = json.loads((ROOT / "src/gamma_archipelago/catalog.json").read_text())
KEY = "a" * 64


def state_for(lua, **options):
    configuration = build_configuration({**defaults(), **options})
    state = lua.globals().gamma_ap_state.new_state()
    state.session_key = KEY
    state.configuration = lua.globals().gamma_ap_configuration.parse(
        encode_configuration(KEY, configuration, expanded=True), KEY, configuration.digest
    )
    state.expanded = True
    state.enabled_checks = lua.globals().gamma_ap_state.enabled_locations(state.configuration)
    state.allowed_items = lua.globals().gamma_ap_state.enabled_items(state.configuration)
    return state


def view(lua, state, psi=True):
    return lua.globals().gamma_ap_tracker.snapshot(state, 3, None, psi)


def rows(view):
    return list(view.rows.values())


@pytest.mark.parametrize("outfit,helmet", [(0, 2), (1, 2), (2, 0), (2, 1), (2, 2)])
@pytest.mark.parametrize("unlock", ["outfit", "helmet"])
def test_upgrade_tracker_allows_carried_equipment_before_equip_unlock(lua, outfit, helmet, unlock):
    state = state_for(
        lua,
        checks_gear_upgrades=1,
        starting_outfit=outfit,
        starting_helmet=helmet,
        starting_firearms=2,
        rewards_starting_gear_unlocks=1,
    )

    def check(id):
        return next(row for row in rows(view(lua, state)) if row.id == id)

    assert check(28052731).status == "available"
    assert check(28052734).status == "available"
    state.unlocks["gear_" + unlock] = True
    assert check(28052734).status == "available"
    state.unlocks.gear_firearms = True
    assert check(28052731).status == "available"


def test_tracker_is_read_only_counts_saved_checks_and_reports_pending_receipts(lua):
    state = state_for(lua)
    state.checks[28052001] = True
    state.received_count = 1
    result = view(lua, state)
    assert result.completed == 1 and result.available == 32 and result.blocked == 0
    assert result.pending == 2 and result.applied == 1
    assert rows(result)[0].status == "completed"
    assert dict(state.checks.items()) == {28052001: True} and state.received_count == 1
    state.session_key = None
    assert not view(lua, state).bound
    state.session_key = KEY
    state.refused_save = True
    assert not view(lua, state).bound
    assert not view(lua, state_for(lua, pda_tracker=0)).enabled


def test_legacy_configuration_without_tracker_option_is_accepted_with_default(lua):
    configuration = build_configuration(defaults())
    packet = encode_configuration(KEY, configuration, expanded=True)
    lines = [line for line in packet.splitlines() if not line.startswith("option|pda_tracker|")]
    lines[-1] = f"end|{len(lines) - 4}"
    result = lua.globals().gamma_ap_configuration.parse(
        "\n".join(lines) + "\n", KEY, configuration.digest
    )
    assert result.options.pda_tracker == 1


def test_tracker_projection_is_generated_from_the_authoritative_catalogue(lua):
    generated = lua.globals().gamma_ap_catalog.tracker_checks
    assert set(generated.keys()) == {row["id"] for row in CATALOG["locations"]}
    for row in CATALOG["locations"]:
        assert generated[row["id"]].name == row["name"]
        assert generated[row["id"]].region == row["level"]
        tasks = row.get("tasks", [])
        required = (
            CATALOG["quest_key_requirements"][CATALOG["quest_gates"][tasks[0]]] if tasks else []
        )
        assert set(generated[row["id"]].quests.values()) == set(required)


def test_zone_and_psi_reasons_and_undirected_route_match_world_connections(lua):
    state = state_for(lua, rewards_zone_keys=1)
    result = view(lua, state)
    assert result.available == 1 and result.blocked == 32
    assert any("Zone access" in row.reason for row in rows(result))
    state.unlocks[lua.globals().gamma_ap_catalog.zone_keys.l03_agroprom] = True
    assert any("connected regions" in row.reason for row in rows(view(lua, state)))
    for permission in lua.globals().gamma_ap_catalog.zone_keys.values():
        state.unlocks[permission] = True
    assert view(lua, state).available == 33
    assert any("psi protection" in row.reason for row in rows(view(lua, state, psi=False)))
    lua.execute(
        "for _,edge in ipairs(gamma_ap_catalog.tracker_connections) do "
        "edge[1],edge[2]=edge[2],edge[1] end"
    )
    assert view(lua, state).available == 33


@pytest.mark.parametrize(
    ("category", "group"),
    [
        ("checks_artefacts", "detector"),
        ("checks_armour_tiers", "outfit"),
        ("checks_weapon_tiers", "firearms"),
        ("checks_knife_tiers", "melee"),
        ("checks_quest_types", "pda"),
        ("checks_side_task_milestones", "pda"),
        ("checks_story_milestones", "pda"),
    ],
)
def test_equipment_requirements_are_explained_then_clear_after_actual_unlock(lua, category, group):
    state = state_for(
        lua, **{category: 1, "starting_" + group: 2, "rewards_starting_gear_unlocks": 1}
    )
    assert any("Equipment permission" in row.reason for row in rows(view(lua, state)))
    state.unlocks["gear_" + group] = True
    assert not any("Equipment permission" in row.reason for row in rows(view(lua, state)))


def test_regional_and_combat_checks_wait_for_matching_requirements(lua):
    state = state_for(lua, checks_mutant_first_kills=1, rewards_zone_keys=1)
    assert any(
        row.status == "available" and row.category == "checks_mutant_first_kills"
        for row in rows(view(lua, state))
    )
    assert any("Regional activity" in row.reason for row in rows(view(lua, state)))
    state = state_for(
        lua,
        checks_mutant_first_kills=1,
        starting_firearms=2,
        starting_melee=2,
        rewards_starting_gear_unlocks=1,
    )
    assert any("firearm or melee" in row.reason for row in rows(view(lua, state)))
    state.unlocks.gear_melee = True
    assert not any("firearm or melee" in row.reason for row in rows(view(lua, state)))


def test_story_quest_dependencies_and_progression_survive_category_filters(lua):
    state = state_for(lua, checks_story_milestones=1, rewards_quest_keys=1)
    assert any("Quest Key:" in row.reason for row in rows(view(lua, state)))
    for permission in lua.globals().gamma_ap_catalog.quest_gates.values():
        state.unlocks[permission] = True
    result = view(lua, state)
    assert not any("Quest Key:" in row.reason for row in rows(result))
    assert any("Unlocked: Quest Key:" in line for line in result.progression.values())
    state.visited_maps[28052001] = True
    for where in lua.globals().gamma_ap_catalog.lab_levels:
        state.visited_maps[lua.globals().gamma_ap_catalog.location_by_level[where]] = True
    assert any(line.startswith("Visited:") for line in view(lua, state).progression.values())


def test_milestone_names_and_bounded_filter_paging(lua):
    state = state_for(lua, checks_kill_milestones=1, checks_side_task_milestones=1)
    result = view(lua, state)
    assert len(result.rows) == 41
    module = lua.globals().gamma_ap_tracker
    first, offset, total = module.page(result, None, None, 1)
    assert len(first) == 4 and offset == 1 and total == 41
    last, offset, total = module.page(result, None, None, 1000)
    assert offset == 41 and len(last) == 1
    assert module.page(result, "Missing region", None, -10)[2] == 0
    assert len(module.page(result, "Global activities", "available", 1)[0]) == 4
    assert len(module.page(result, None, "completed", None)[0]) == 0


def test_game_exposes_only_a_detached_projection_and_handles_unavailable_psi_api(lua):
    game, engine = load_game(lua)
    set_incoming(engine)
    game.actor_on_update()
    assert game.tracker_view().pending == 2
    lua.execute("db.actor.object=function() return {condition=function() return 1 end} end")
    result = game.tracker_view()
    assert any("psi protection: usable" in line for line in result.progression.values())
    result.rows[1].status = "changed"
    assert game.tracker_view().rows[1].status != "changed"


def test_progression_groups_are_sorted_detached_and_preserve_every_legacy_entry(lua):
    state = state_for(lua, rewards_zone_keys=1, rewards_progressive_tools=1, rewards_convenience=1)
    state.unlocks.zone_l02_garbage = True
    result = view(lua, state)
    groups = result.progression_groups
    flattened = []
    for entries in groups.values():
        values = list(entries.values())
        assert values == sorted(values)
        flattened.extend(values)
    assert sorted(flattened) == sorted(result.progression.values())
    assert all(text.startswith("Unlocked:") for text in groups.unlocked.values())
    assert all(text.startswith("Locked:") for text in groups.locked.values())
    assert len(groups.unlocked) == 1 and len(groups.locked) > 0
    assert len(groups.exploration) == len(list(lua.globals().gamma_ap_catalog.lab_levels.keys()))
    assert any("Progressive tools" in text for text in groups.status.values())
    assert any("carry permission" in text for text in groups.status.values())
    groups.unlocked[1] = "Changed UI copy"
    assert view(lua, state).progression_groups.unlocked[1] != "Changed UI copy"
    assert dict(state.unlocks.items()) == {"zone_l02_garbage": True}
    assert not list(state.checks.keys())
