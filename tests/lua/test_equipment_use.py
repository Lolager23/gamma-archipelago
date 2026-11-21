import pytest

from gamma_archipelago.configuration import encode_configuration
from gamma_archipelago.protocol import encode_incoming

from .test_game_adapter import saved_state
from .test_gear_locks import gear_game
from .test_loadout import CONFIG_PATH, KEY, configured_game
from .test_stashes import poll, progress

GROUPS = [
    ("pda", "D_PDA", "i_device", 8),
    ("detector", "DET_SIMP", "i_device", 9),
    ("firearms", "WP_PM", "w_pistol", 2),
    ("melee", "WP_KNIFE", "w_melee", 1),
    ("outfit", "E_STLK", "o_light", 7),
    ("helmet", "E_HLMET", "o_helmet", 12),
    ("backpack", "EQ_BAKPK", "i_backpack", 13),
    ("tools", "II_ATTCH", "i_tool", 11),
    ("utilities", "WP_BINOC", "i_device", 5),
]


def use_game(lua, group="pda"):
    game, engine, configuration = configured_game(
        lua, **{"starting_" + group: 2, "rewards_starting_gear_unlocks": 1}
    )
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    game.on_game_start()
    engine.creation.new_game_faction = None
    poll(game, engine)
    return game, engine


@pytest.mark.parametrize("group,cls,kind,slot", GROUPS)
def test_locked_gear_is_carried_stowed_and_usable_only_after_unlock(lua, group, cls, kind, slot):
    game, engine = use_game(lua, group)
    item = lua.globals().add_item(50, "locked_item", cls, kind, 0)
    flags = lua.table(ret_value=True)
    game.actor_on_item_before_pickup(item, flags)
    assert flags.ret_value is True
    game.actor_on_item_take(item)
    game.actor_on_item_take_from_box(None, item)
    assert engine.objects[50] is not None
    engine.slots[slot] = item
    game.actor_item_to_slot(item)
    assert engine.slots[slot] is None and engine.objects[50] is not None
    game.actor_on_item_before_use(item, flags)
    assert flags.ret_value is False
    data = saved_state(lua, game)
    data.gamma_archipelago_v1.unlocks["gear_" + group] = True
    game.load_state(data)
    engine.slots[slot] = item
    game.actor_item_to_slot(item)
    flags.ret_value = True
    game.actor_on_item_before_use(item, flags)
    assert flags.ret_value is True and engine.slots[slot] is not None


@pytest.mark.parametrize("failure", [None, "fail_stow", "ignore_stow"])
def test_poll_enforces_scripted_and_restored_equipment_without_dropping_it(lua, failure):
    game, engine = use_game(lua)
    item = lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    engine.slots[8] = item
    if failure:
        engine[failure] = True
    poll(game, engine)
    assert engine.objects[50] is not None
    assert (engine.slots[8] is not None) == bool(failure)
    if failure:
        assert "stowing failed" in list(engine.logs.values())[-1]
    else:
        data = saved_state(lua, game)
        game.load_state(data)
        engine.slots[8] = item
        poll(game, engine)
        assert engine.slots[8] is None and engine.objects[50] is not None


def test_slot_failure_does_not_prevent_the_permission_receipt(lua):
    game, engine = gear_game(lua, items=())
    poll(game, engine)
    item = lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    engine.slots[8] = item
    engine.fail_stow = True
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = encode_incoming(
        KEY, (28051602,), engine.configuration_key
    )
    poll(game, engine)
    assert progress(lua, game).unlocks.gear_pda and progress(lua, game).received_count == 1
    assert engine.objects[50] is not None


def test_another_mod_reequipping_during_stow_cannot_recurse_or_destroy_the_item(lua):
    game, engine = use_game(lua)
    item = lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    engine.slots[8] = item
    lua.execute("""
        engine.stow_calls=0
        db.actor.move_to_ruck=function(self,item)
            engine.stow_calls=engine.stow_calls+1
            engine.callbacks.actor_item_to_slot(item)
        end
    """)
    game.actor_item_to_slot(item)
    assert engine.stow_calls == 1 and engine.objects[50] is not None
    assert any("re-equipped" in text for text in engine.logs.values())


def test_before_session_binding_does_not_strip_loaded_permission_equipment(lua):
    game, engine = use_game(lua)
    item = lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    state = lua.globals().gamma_ap_state.new_state()
    state.configuration = progress(lua, game).configuration
    engine.slots[8] = item
    assert lua.globals().gamma_ap_gear_locks.equipped(state, item) is True
    assert engine.slots[8] is not None


def install_native_ui(lua, game, engine):
    lua.execute("""
        engine.calls={};engine.warnings={}
        local function native(name)
            return function(...)
                engine.calls[#engine.calls+1]={name,...};return 'native',nil,3
            end
        end
        ui_inventory={UIInventory={Cond_Equip=native('condition'),Action_Equip=native('equip'),
            Action_Use=native('use'),Action_Custom=native('custom')}}
        pda={pda_use=native('pda')}
        item_device={drain_device_on_event=native('drain'),set_nightvision=native('night')}
        actor_menu={set_msg=function(_,message) engine.warnings[#engine.warnings+1]=message end}
        game={translate_string=function(key) return key end}
        key_bindings={kWPN_FIRE=1,kWPN_RELOAD=2,kWPN_ZOOM=3,kTORCH=4}
    """)
    poll(game, engine)
    engine.callbacks.on_loading_screen_dismissed()
    engine.frame += 1
    return lua.globals().gamma_ap_equipment_use


@pytest.mark.parametrize("action", ["Cond_Equip", "Action_Equip", "Action_Use", "Action_Custom"])
@pytest.mark.parametrize("numeric", [False, True])
def test_inventory_guards_deny_before_native_action_and_preserve_delegate_arguments(
    lua, action, numeric
):
    game, engine = use_game(lua)
    module = install_native_ui(lua, game, engine)
    item = lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    argument = 50 if numeric else item
    callback = lua.globals().ui_inventory.UIInventory[action]
    assert callback(lua.table(), argument, "actor_bag", 7) is False
    assert not len(engine.calls)
    assert engine.objects[50] is not None
    data = saved_state(lua, game)
    data.gamma_archipelago_v1.unlocks.gear_pda = True
    game.load_state(data)
    assert callback(lua.table(), argument, "actor_bag", 7) == ("native", None, 3)
    assert engine.calls[1][4] == "actor_bag" and engine.calls[1][5] == 7
    assert module is not None


def test_custom_actions_allow_maintenance_of_a_locked_weapon(lua):
    game, engine = use_game(lua, "firearms")
    install_native_ui(lua, game, engine)
    item = lua.globals().add_item(50, "gun", "WP_PM", "w_pistol", 0)
    callback = lua.globals().ui_inventory.UIInventory.Action_Custom
    assert callback(lua.table(), item, "actor_bag", 1) == ("native", None, 3)


def test_locked_devices_can_be_recharged_without_enabling_their_use(lua):
    game, engine = use_game(lua)
    install_native_ui(lua, game, engine)
    item = lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    engine.meta.pda.use1_action_functor = "item_device.func_battery"
    assert lua.globals().ui_inventory.UIInventory.Action_Custom(
        lua.table(), item, "actor_bag", None, 1
    ) == ("native", None, 3)
    assert lua.globals().pda.pda_use() is False


@pytest.mark.parametrize("group", ["tools", "utilities", "detector"])
def test_locked_custom_tool_and_device_actions_do_not_execute(lua, group):
    game, engine = use_game(lua, group)
    install_native_ui(lua, game, engine)
    _, cls, kind, _ = next(row for row in GROUPS if row[0] == group)
    item = lua.globals().add_item(50, "tool", cls, kind, 0)
    assert (
        lua.globals().ui_inventory.UIInventory.Action_Custom(lua.table(), item, "actor_bag", 1)
        is False
    )
    assert not len(engine.calls)


def test_pda_inventory_presence_does_not_enable_native_pda_before_permission(lua):
    game, engine = use_game(lua)
    install_native_ui(lua, game, engine)
    lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    assert lua.globals().pda.pda_use("arg") is False
    assert lua.globals().gamma_ap_loadout.pda_available(progress(lua, game)) is False
    data = saved_state(lua, game)
    data.gamma_archipelago_v1.unlocks.gear_pda = True
    game.load_state(data)
    assert lua.globals().pda.pda_use("arg") == ("native", None, 3)
    assert lua.globals().gamma_ap_loadout.pda_available(progress(lua, game)) is True


def test_rucksack_device_events_and_nightvision_cannot_bypass_permission(lua):
    game, engine = use_game(lua, "utilities")
    install_native_ui(lua, game, engine)
    item = lua.globals().add_item(50, "device_torch", "TORCH_S", "i_device", 0)
    assert lua.globals().item_device.drain_device_on_event(item, "sec", 2) is False
    lua.globals().device_item = item
    lua.execute("db.actor.object=function(self,section) return section=='sec' and device_item end")
    assert lua.globals().item_device.drain_device_on_event(None, "sec", 2) is False
    assert lua.globals().item_device.set_nightvision("sec", True) is False
    assert lua.globals().item_device.set_nightvision("sec", False) == ("native", None, 3)
    data = saved_state(lua, game)
    data.gamma_archipelago_v1.unlocks.gear_utilities = True
    game.load_state(data)
    assert lua.globals().item_device.drain_device_on_event(item, "sec", 2) == ("native", None, 3)
    assert lua.globals().item_device.set_nightvision("sec", True) == ("native", None, 3)


def test_disappeared_inventory_item_is_refused_before_native_methods(lua):
    game, engine = use_game(lua)
    install_native_ui(lua, game, engine)
    for name in ("Cond_Equip", "Action_Equip", "Action_Use", "Action_Custom"):
        assert lua.globals().ui_inventory.UIInventory[name](lua.table(), 60000) is False
    assert not len(engine.calls)


@pytest.mark.parametrize("binding", [1, 2, 3])
def test_weapon_input_veto_preserves_other_mod_flags(lua, binding):
    game, engine = use_game(lua, "firearms")
    install_native_ui(lua, game, engine)
    engine.active = lua.globals().add_item(50, "gun", "WP_PM", "w_pistol", 0)
    flags = lua.table(ret_value=True)
    engine.callbacks.on_before_key_press(0, binding, False, flags)
    assert flags.ret_value is False
    data = saved_state(lua, game)
    data.gamma_archipelago_v1.unlocks.gear_firearms = True
    game.load_state(data)
    engine.callbacks.on_before_key_hold(0, binding, False, flags)
    assert flags.ret_value is False
    flags.ret_value = True
    engine.callbacks.on_before_key_press(0, binding, False, flags)
    assert flags.ret_value is True


def test_other_input_and_torch_veto_and_loading_safe_warning_throttle(lua):
    game, engine = use_game(lua, "utilities")
    module = install_native_ui(lua, game, engine)
    flags = lua.table(ret_value=True)
    game.on_before_key(0, 99, False, flags)
    game.on_before_key(0, None, False, flags)
    assert flags.ret_value is True
    game.on_before_key(0, 4, False, flags)
    assert flags.ret_value is False and len(engine.warnings) == 1
    module.warn()
    assert len(engine.warnings) == 1
    engine.now += 1000
    lua.globals().gamma_ap_readiness.reset()
    module.warn()
    assert len(engine.warnings) == 1
    engine.callbacks.on_loading_screen_dismissed()
    engine.frame += 1
    module.warn()
    assert len(engine.warnings) == 2
    lua.globals().key_bindings = None
    game.on_before_key(0, 4, False, flags)


def test_warning_api_failure_does_not_allow_the_locked_action_or_crash_its_callback(lua):
    game, engine = use_game(lua)
    install_native_ui(lua, game, engine)
    item = lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    lua.execute("actor_menu.set_msg=function() error('UI unavailable') end")
    assert lua.globals().ui_inventory.UIInventory.Action_Use(lua.table(), item) is False
    assert any("Cannot display" in message for message in engine.logs.values())


@pytest.mark.parametrize("disabled,hud_free", [(True, True), (False, False)])
def test_menu_captured_or_disabled_input_is_preserved_while_world_fire_stays_locked(
    lua, disabled, hud_free
):
    game, engine = use_game(lua, "firearms")
    install_native_ui(lua, game, engine)
    engine.active = lua.globals().add_item(50, "gun", "WP_PM", "w_pistol", 0)
    engine.hud_free = hud_free
    lua.execute("actor_menu.is_hud_free=function() return engine.hud_free end")
    flags = lua.table(ret_value=True)
    game.on_before_key(0, 1, disabled, flags)
    assert flags.ret_value is True
    engine.hud_free = True
    game.on_before_key(0, 1, False, flags)
    assert flags.ret_value is False


def test_wrappers_are_idempotent_preserve_another_mod_and_rebind_to_current_state(lua):
    game, engine = use_game(lua)
    install_native_ui(lua, game, engine)
    callback = lua.globals().ui_inventory.UIInventory.Action_Equip
    poll(game, engine)
    assert lua.eval("function(a,b) return a==b end")(
        callback, lua.globals().ui_inventory.UIInventory.Action_Equip
    )
    lua.execute("""
        local delegate=ui_inventory.UIInventory.Action_Equip
        ui_inventory.UIInventory.Action_Equip=function(...)
            engine.other=true;return delegate(...)
        end
    """)
    poll(game, engine)
    allowed = lua.globals().add_item(50, "knife", "WP_KNIFE", "w_melee", 0)
    assert lua.globals().ui_inventory.UIInventory.Action_Equip(lua.table(), allowed) == (
        "native",
        None,
        3,
    )
    assert engine.other
    getter = lua.eval(
        "function() return {unlocks={gear_pda=true},"
        "configuration={expanded=true,options={starting_pda=2}}} end"
    )
    lua.globals().gamma_ap_equipment_use.install(getter)
    assert lua.globals().pda.pda_use() == ("native", None, 3)
