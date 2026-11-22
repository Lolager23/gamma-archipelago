import pytest

from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.discovery import configured_location_ids

from .test_tracker import state_for


def weather_state(lua):
    state = state_for(lua, checks_emissions=1, checks_psi_storms=1)
    lua.execute("""gamma_ap_readiness.ready=function() return ready end
        ready=false;level={name=function() return where end};where='l01_escape'
        emission=false;storm=false
        surge_manager={is_started=function() return emission end}
        psi_storm_manager={is_started=function() return storm end}""")
    return state


def test_weather_waits_for_an_active_surface_world_and_is_saved_monotonically(lua):
    state = weather_state(lua)
    module = lua.globals().gamma_ap_weather
    lua.globals().emission = True
    assert module.poll(state) and not state.checks[28053001]
    lua.globals().ready = True
    lua.globals().where = "l10u_bunker"
    assert module.poll(state) and not state.checks[28053001]
    lua.globals().where = "l01_escape"
    assert module.poll(state) and state.checks[28053001] and not state.checks[28053002]
    lua.globals().storm = True
    assert module.poll(state) and state.checks[28053002]
    lua.globals().emission = False
    assert module.poll(state) and state.checks[28053001]


@pytest.mark.parametrize("value", [None, "bad", "error"])
def test_missing_or_invalid_weather_api_fails_closed(lua, value):
    state = weather_state(lua)
    lua.globals().ready = True
    if value is None:
        lua.globals().surge_manager = None
    elif value == "error":
        lua.execute("surge_manager.is_started=function() error('bad') end")
    else:
        lua.globals().emission = value
    ok, message = lua.globals().gamma_ap_weather.poll(state)
    assert not ok and message and not state.checks[28053001]


def test_infinite_stamina_is_opt_in_bound_and_requires_the_native_world_gate(lua):
    state = weather_state(lua)
    lua.execute("db={actor={power=0.25}}")
    module = lua.globals().gamma_ap_stamina
    assert module.poll(state) and lua.globals().db.actor.power == 0.25
    state.configuration.options.infinite_stamina = 1
    assert module.poll(state) and lua.globals().db.actor.power == 0.25
    lua.globals().ready = True
    assert module.poll(state) and lua.globals().db.actor.power == 1
    state.refused_save = True
    lua.globals().db.actor.power = 0.1
    assert module.poll(state) and lua.globals().db.actor.power == 0.1
    state.refused_save = False
    lua.execute("db.actor=setmetatable({},{__newindex=function() error('no power API') end})")
    assert not module.poll(state)[0]


@pytest.mark.parametrize("content", [0, 1])
@pytest.mark.parametrize("ms,oa", [(0, 0), (1, 0), (0, 1), (1, 1)])
def test_arc_and_artefact_manifests_match_the_python_owner(lua, content, ms, oa):
    values = dict(
        checks_story_milestones=1,
        checks_mortal_sin=ms,
        checks_operation_afterglow=oa,
        checks_artefacts=1,
        checks_weapon_tiers=1,
        artefact_discovery_count=60,
        content_progression=content,
    )
    state = state_for(lua, **values)
    assert set(state.enabled_checks) == configured_location_ids(
        build_configuration(defaults() | values)
    )


def test_tool_stash_tiers_and_terminal_story_goals_use_existing_state(lua):
    state = state_for(lua, rewards_progressive_tools=1)
    state.applied_items = lua.table_from([28051204])
    assert lua.globals().gamma_ap_workshop.tools_level(state) == 0
    state.applied_items[2] = 28051202
    assert lua.globals().gamma_ap_workshop.tools_level(state) == 1
    state.applied_items[3] = 28051203
    assert lua.globals().gamma_ap_workshop.tools_level(state) == 3
    for goal, id in ((7, 28052643), (8, 28052653)):
        state.configuration.options.goal = goal
        state.goal_complete = False
        assert lua.globals().gamma_ap_goals.poll(state) and not state.goal_complete
        state.tasks.stories[id] = True
        assert lua.globals().gamma_ap_goals.poll(state) and state.goal_complete


def test_tool_stash_contents_are_physical_and_do_not_grant_psi_permission(lua):
    from .test_game_adapter import saved_state
    from .test_stashes import poll, progress, stash_game

    game, engine = stash_game(
        lua, items=(28051202, 28051203, 28051204), rewards_progressive_tools=1
    )
    lua.execute("""local native=function() return true end
        ui_workshop={UIWorkshopRepair={Repair=native},UIWorkshopUpgrade={Upgrade=native},UIWorkshopCraft={Craft=native}}
        item_repair={UIRepair={OnRepair=native}}
        ui_inventory={UIInventory={RMode_RepairYes=native,RMode_UpgradeYes=native}}""")
    for id, name in enumerate(("esc_treasure_2", "esc_treasure_10", "esc_treasure_17"), 20):
        lua.globals().make_cache(id, name, "l01_escape", 65535, "invbox")
    for _ in range(3):
        poll(game, engine)
    state = progress(lua, game)
    assert state.received_count == 3
    for receipt, section in enumerate(("itm_basickit", "itm_advancedkit", "itm_expertkit"), 1):
        record = state.stashes.records[receipt]
        assert engine.markers[f"{record.cache_id}:gamma_ap_progression"]
        game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
        filled = progress(lua, game).stashes.records[receipt]
        assert filled.actions[1].section == section
        assert engine.spawns[filled.actions[1].created_id].owner == record.cache_id
    assert not progress(lua, game).unlocks.calibrated_psi
    game.load_state(saved_state(lua, game))
    assert not progress(lua, game).refused_save
    assert engine.spawn_calls == 3


@pytest.mark.parametrize(
    "repair_type,identity",
    [("pistol", 28052751), ("shotgun", 28052752), ("rifle_5", 28052753), ("rifle_7", 28052754)],
)
def test_actual_weapon_repair_type_reports_its_grade_without_relabelling_role_checks(
    lua, repair_type, identity
):
    from .test_equipment_checks import equipment_game, gear, poll, progress

    game, engine, _ = equipment_game(lua, checks_weapon_tiers=1, playability_logic=0)
    engine.active = gear(lua)
    engine.meta["test_pistol"].repair_type = repair_type
    poll(game, engine)
    assert progress(lua, game).checks[identity]


def test_melter_projection_is_independent_of_the_combat_pacing_toggle(lua):
    state = state_for(
        lua,
        checks_artefacts=1,
        rewards_artefact_melter=1,
        playability_logic=0,
        starting_tools=2,
        rewards_starting_gear_unlocks=1,
    )
    module = lua.globals().gamma_ap_playability
    row = lua.table_from(dict(category="checks_artefacts", quota="artefact", minimum=21))
    regions = lua.table_from({})
    assert "Melter required" in module.reason(state, row, regions, False)
    state.applied_items = lua.table_from([28051802])
    assert "tools" in module.reason(state, row, regions, False)
    state.unlocks.gear_tools = True
    assert module.reason(state, row, regions, False) is None


def test_melter_delivery_spawns_the_approved_item_without_expanding_legacy_section_ids(lua):
    from .test_stashes import poll, progress, stash_game

    game, engine = stash_game(lua, items=(28051802,), rewards_artefact_melter=1)
    poll(game, engine)
    assert progress(lua, game).received_count == 1
    assert engine.spawn_calls == 1
    assert next(iter(engine.spawns.values())).section == "itm_artefactskit"
    assert len(progress(lua, game).stashes.order) == 0


def test_friendly_trader_goodwill_has_a_permanent_ap_earned_floor(lua):
    from .test_settlement_access import native

    state = state_for(lua, checks_faction_standing=1, rewards_faction_reputation=1)
    native(lua, goodwill=-3000)
    lua.execute("db={actor={id=function() return 0 end}}")
    state.applied_items = lua.table_from([28051301] * 12)
    assert lua.globals().gamma_ap_reputation.reconcile(state)
    assert lua.globals().goodwill == 3000
    lua.globals().goodwill = -2000
    assert lua.globals().gamma_ap_reputation.reconcile(state)
    assert lua.globals().goodwill == 3000


def test_late_equipment_checks_wait_but_the_equipment_itself_is_not_restricted(lua):
    from .test_equipment_checks import equipment_game, gear, progress

    game, engine, _ = equipment_game(
        lua, checks_weapon_tiers=1, checks_armour_tiers=1, rewards_faction_reputation=1
    )
    engine.outfit = gear(lua, 2, "army_nosorog_outfit", "o_heavy")
    engine.active = gear(lua, 3, "test_rifle", "w_rifle")
    engine.meta["test_rifle"].repair_type = "rifle_7"
    state = progress(lua, game)
    module = lua.globals().gamma_ap_equipment_checks
    assert module.poll(state, state.configuration)
    assert state.checks[28052701] and state.checks[28052702]
    assert not state.checks[28052703] and not state.checks[28052704] and not state.checks[28052754]
    assert not lua.globals().gamma_ap_gear_locks.locked(state, engine.outfit)
    state.applied_items = lua.table_from([28051307] * 8)
    assert module.poll(state, state.configuration) and not state.checks[28052754]
    state.applied_items = lua.table_from([28051301] * 8)
    assert module.poll(state, state.configuration)
    assert state.checks[28052703] and state.checks[28052704] and state.checks[28052754]


def test_conditional_artefact_manifest_matches_python_and_rejects_invalid_extra(lua):
    from gamma_archipelago.catalog import MAP_LOCATION_IDS
    from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
    from gamma_archipelago.discovery import configured_location_ids

    from .test_loadout import KEY

    configuration = build_configuration(
        {
            **defaults(),
            "checks_artefacts": 1,
            "rewards_artefact_melter": 1,
            "artefact_overflow_count": 7,
        }
    )
    parsed = lua.globals().gamma_ap_configuration.parse(
        encode_configuration(KEY, configuration, expanded=True), KEY, configuration.digest
    )
    assert parsed is not None
    selected = lua.globals().gamma_ap_discovery.select(parsed, lua.table())
    assert set(selected) == set(configured_location_ids(configuration)) - MAP_LOCATION_IDS
    for key, value in [
        ("content_progression", 0),
        ("artefact_discovery_mode", 0),
        ("checks_artefacts", 0),
        ("artefact_discovery_count", 20),
        ("artefact_extra_ceiling", 40),
        ("rewards_artefact_melter", 0),
    ]:
        copied = lua.globals().gamma_ap_configuration.copy(parsed)
        copied.options[key] = value
        result, reason = lua.globals().gamma_ap_discovery.select(copied, lua.table())
        assert result is None and "capacity" in reason
