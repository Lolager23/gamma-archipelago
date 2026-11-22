import pytest

from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.content_progression import configured_item_ids
from gamma_archipelago.protocol import encode_incoming

from .test_equipment_use import install_native_ui
from .test_loadout import KEY
from .test_workshop import INCOMING, craft_dialog, poll, state_of, tool_game

KITS = [
    (28051831, "basic", "itm_basickit", "start_workshop_basic"),
    (28051832, "advanced", "itm_advancedkit", "start_workshop_advanced"),
    (28051833, "expert", "itm_expertkit", "start_workshop_expert"),
    (28051834, "medical", "itm_drugkit", "start_workshop_medic"),
    (28051835, "ammo", "itm_ammokit", "start_workshop_ammo"),
    (28051836, "artefact", "itm_artefactskit", "start_workshop_artefacts"),
]


def kit_game(lua, items=(), **options):
    return tool_game(
        lua,
        items,
        **{
            "tool_use_permissions": 1,
            "rewards_drug_making_tools": 1,
            "rewards_gunsmithing_tools": 1,
            "rewards_artefact_melter": 1,
            "permission_supplies": 0,
            **options,
        },
    )


def restore(lua, game, **unlocks):
    state = state_of(lua, game)
    for name, value in unlocks.items():
        state.unlocks[name] = value
    game.load_state(lua.table(gamma_archipelago_v1=state))


def test_six_rewards_deliver_free_kits_without_optional_supplies_and_never_repeat_on_reload(lua):
    ids = tuple(row[0] for row in KITS)
    game, engine, _ = kit_game(lua, ids + ids)
    for _ in range(11):
        poll(game, engine)
    state = state_of(lua, game)
    assert list(engine.created.values()) == [row[2] for row in KITS]
    assert state.received_count == 12
    assert all(state.unlocks["tool_" + row[1]] for row in KITS)
    assert lua.globals().gamma_ap_tool_permissions.melter_received(state)
    assert lua.globals().gamma_ap_workshop.tools_level(state) == 3
    game.load_state(lua.table(gamma_archipelago_v1=state))
    poll(game, engine)
    assert list(engine.created.values()) == [row[2] for row in KITS]
    assert not state_of(lua, game).refused_save


def test_failed_free_kit_defers_unlock_and_retries_after_save_load(lua):
    game, engine, config = kit_game(lua)
    engine.fail_reward = True
    engine.files[INCOMING] = encode_incoming(KEY, (28051831,), config.digest)
    poll(game, engine)
    state = state_of(lua, game)
    assert not state.unlocks.tool_basic and state.received_count == 0
    assert state.deliveries[1].next_action == 1
    game.load_state(lua.table(gamma_archipelago_v1=state))
    engine.fail_reward = False
    poll(game, engine)
    assert state_of(lua, game).unlocks.tool_basic
    assert list(engine.created.values()) == ["itm_basickit"]


@pytest.mark.parametrize("id_,key,section,shortcut", KITS)
def test_looting_carrying_and_crafting_a_kit_never_grants_use_permission(
    lua, id_, key, section, shortcut
):
    game, engine, _ = kit_game(lua)
    item = lua.globals().add_item(50, section, "II_ATTCH", "i_kit", 0)
    flags = lua.table(ret_value=True)
    game.actor_on_item_before_pickup(item, flags)
    assert flags.ret_value is True
    game.actor_on_item_take(item)
    game.actor_on_item_take_from_box(None, item)
    game.actor_on_item_before_use(item, flags)
    assert flags.ret_value is False and engine.objects[50] is not None
    assert not state_of(lua, game).unlocks["tool_" + key]
    restore(lua, game, **{"tool_basic": True, "tool_advanced": True, "tool_" + key: True})
    flags.ret_value = True
    game.actor_on_item_before_use(item, flags)
    assert flags.ret_value is True and engine.objects[50] is not None
    flags.ret_value = False  # Preserve another mod's veto.
    game.actor_on_item_before_use(item, flags)
    assert flags.ret_value is False
    game.actor_on_item_before_use(None, flags)


def test_crafting_locked_advanced_kit_uses_input_basic_permission_not_output_permission(lua):
    game, engine, _ = kit_game(lua, (28051831,))
    dialog = craft_dialog(lua, 1)
    dialog.section = "itm_advancedkit"
    api = lua.globals().ui_workshop.UIWorkshopCraft
    assert api.Craft(dialog) == "native"
    assert api.Craft(craft_dialog(lua, 2)) is False
    assert api.Craft(craft_dialog(lua, 4)) is False
    restore(lua, game, tool_medical=True)
    assert api.Craft(craft_dialog(lua, 4)) == "native"
    assert not state_of(lua, game).unlocks.tool_advanced
    assert engine.work_calls == 2


@pytest.mark.parametrize("action", ["Action_Equip", "Action_Use", "Action_Custom"])
def test_inventory_actions_enforce_kit_use_without_consuming_it(lua, action):
    game, engine, _ = kit_game(lua)
    install_native_ui(lua, game, engine)
    lua.execute("""
        ui_inventory.UIInventory.RMode_RepairYes=function() return 'native' end
        ui_inventory.UIInventory.RMode_UpgradeYes=function() return 'native' end
    """)
    poll(game, engine)
    item = lua.globals().add_item(50, "itm_drugkit", "II_ATTCH", "i_kit", 0)
    call = lua.globals().ui_inventory.UIInventory[action]
    assert call(lua.table(), 50, "bag", 7, 1) is False
    assert not list(engine.calls.values()) and engine.objects[50] is not None
    assert engine.warnings[1]
    restore(lua, game, tool_medical=True)
    assert call(lua.table(), item, "bag", 7, 1) == ("native", None, 3)


def test_six_native_shortcuts_compose_reinstall_and_preserve_arguments(lua):
    game, engine, _ = kit_game(lua)
    lua.execute("""
        workshop_tool={}
        local names={'basic','advanced','expert','medic','ammo','artefacts'}
        for _,name in ipairs(names) do
            workshop_tool['start_workshop_'..name]=function(...) return 'native',nil,... end
        end
    """)
    poll(game, engine)
    for _, _, _, shortcut in KITS:
        assert lua.globals().workshop_tool[shortcut](7) is False
    restore(lua, game, **{"tool_" + row[1]: True for row in KITS})
    poll(game, engine)
    for _, _, _, shortcut in KITS:
        assert lua.globals().workshop_tool[shortcut](7) == ("native", None, 7)
    lua.execute("""
        local previous=workshop_tool.start_workshop_basic
        workshop_tool.start_workshop_basic=function(...) return previous(...) end
        workshop_tool.start_workshop_medic=nil
    """)
    poll(game, engine)
    assert lua.globals().workshop_tool.start_workshop_basic(8) == ("native", None, 8)


def test_class_c_check_and_tracker_wait_for_advanced_even_when_firearm_is_usable(lua):
    game, engine, _ = kit_game(
        lua, (28051831,), checks_weapon_tiers=1, playability_logic=0, checks_gear_upgrades=0
    )
    # Use the same native shape as equipment-check tests, without launching the engine.
    lua.execute("""
        make_gear=function()
            return {section=function() return 'test_rifle' end, condition=function() return 1 end}
        end
    """)
    engine.meta.test_rifle = lua.table(kind="w_rifle", repair_type="rifle_5")
    engine.active = lua.globals().make_gear()
    poll(game, engine)
    catalog = lua.globals().gamma_ap_catalog
    id_ = catalog.weapon_grade_locations.rifle_5
    assert not state_of(lua, game).checks[id_]
    row = catalog.tracker_checks[id_]
    module = lua.globals().gamma_ap_tool_permissions
    assert module.grade_reason(state_of(lua, game), row)
    restore(lua, game, tool_advanced=True)
    poll(game, engine)
    assert state_of(lua, game).checks[id_]
    assert module.grade_reason(state_of(lua, game), row) is None


@pytest.mark.parametrize("mode", [0, 1])
def test_python_and_lua_item_manifests_match_for_old_and_new_seeds(lua, mode):
    from .test_tracker import state_for

    options = dict(
        tool_use_permissions=mode,
        equipment_class_progression=0,
        progressive_tool_receipts=0,
        rewards_progressive_tools=1,
        rewards_drug_making_tools=1,
        rewards_gunsmithing_tools=1,
        rewards_artefact_melter=1,
        rewards_progression_stashes=1,
    )
    state = state_for(lua, **options)
    configuration = build_configuration(defaults() | options)
    assert set(state.allowed_items) == configured_item_ids(configuration)
    module = lua.globals().gamma_ap_tool_permissions
    assert module.reason(state, "unknown") is None
    assert module.section_reason(state, "not_a_kit") is None
    assert module.grade_reason(state, lua.table()) is None
    if mode:
        state.unlocks.tool_expert = True
        assert module.level(state) == 0
        assert module.reason(state, "expert")
        state.session_key = None
        assert "session" in module.reason(state, "basic")
        state.configuration.options.rewards_progressive_tools = 0
        assert module.reason(state, "basic") is None
    else:
        assert module.reason(state, "basic") is None


def test_disabled_content_and_missing_configuration_keep_native_use(lua):
    game, _, _ = kit_game(lua, content_progression=0)
    module = lua.globals().gamma_ap_tool_permissions
    assert module.reason(state_of(lua, game), "basic") is None
    assert not module.enabled(None)
    assert not module.any_enabled(None)
    assert not module.any_enabled(state_of(lua, game).configuration)
    lua.execute("""
        workshop_tool=setmetatable({},{__index=function()
            error('disabled toolkit integration touched')
        end})
    """)
    getter = lua.eval("function(state) return function() return state end end")(state_of(lua, game))
    lua.globals().gamma_ap_tool_use.install(getter)


def test_specialist_only_seeds_activate_guards_and_legacy_melter_history_still_works(lua):
    game, _, _ = kit_game(lua, rewards_progressive_tools=0)
    state = state_of(lua, game)
    module = lua.globals().gamma_ap_tool_permissions
    assert module.any_enabled(state.configuration)
    assert lua.globals().gamma_ap_workshop.allowed(state, "craft", craft_dialog(lua, 4))[0] is False
    for row in lua.globals().gamma_ap_catalog.tool_use_items.values():
        state.configuration.options[row.category] = 0
    assert not module.any_enabled(state.configuration)
    state.configuration.options.tool_use_permissions = 0
    assert not module.melter_received(state)
    state.applied_items = lua.table_from([28051003, 28051802])
    assert module.melter_received(state)


def test_new_melter_tracker_requires_its_own_permission_without_general_tools(lua):
    from .test_tracker import state_for

    state = state_for(
        lua,
        rewards_artefact_melter=1,
        starting_tools=2,
        rewards_starting_gear_unlocks=1,
        playability_logic=0,
    )
    module = lua.globals().gamma_ap_playability
    row = lua.table(category="checks_artefacts", quota="artefact", minimum=21)
    assert "Melter required" in module.reason(state, row, lua.table(), False)
    state.unlocks.tool_artefact = True
    assert module.reason(state, row, lua.table(), False) is None


def test_kit_warnings_use_translatable_labels_and_english_fallback(lua):
    game, _, _ = kit_game(lua)
    module = lua.globals().gamma_ap_tool_permissions
    lua.execute("""
        game={translate_string=function(key)
            if key=='gamma_ap_tool_permission_required' then return 'Permission: ' end
            if key=='gamma_ap_reward_28051831' then return 'Basic kit' end
            return key
        end}
    """)
    assert module.reason(state_of(lua, game), "basic") == "Permission: Basic kit"
    lua.execute("game.translate_string=function() return '' end")
    assert "Tool Use: Basic Tools" in module.reason(state_of(lua, game), "basic")
    lua.execute("game.translate_string=nil")
    state = state_of(lua, game)
    state.refused_save = True
    assert "valid AP session" in module.reason(state, "basic")


def test_uncertain_free_kit_blocks_automatic_replay_and_permission(lua):
    game, engine, config = kit_game(lua)
    lua.execute(
        "alife_create_item=function() engine.attempts=(engine.attempts or 0)+1; return true end"
    )
    engine.files[INCOMING] = encode_incoming(KEY, (28051835,), config.digest)
    poll(game, engine)
    state = state_of(lua, game)
    assert state.deliveries[1].uncertain and not state.unlocks.tool_ammo
    game.load_state(lua.table(gamma_archipelago_v1=state))
    poll(game, engine)
    assert engine.attempts == 1 and not state_of(lua, game).unlocks.tool_ammo
