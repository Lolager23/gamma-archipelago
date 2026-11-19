import pytest

from gamma_archipelago.configuration import encode_configuration
from gamma_archipelago.protocol import encode_incoming

from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, KEY, configured_game

TOOLS = 28051801
INCOMING = "D:/AnomalyAP/appdata/archipelago\\incoming.txt"


def tool_game(lua, items=(), **options):
    game, engine, configuration = configured_game(
        lua, **{"rewards_progressive_tools": 1, "checks_gear_upgrades": 1, **options}
    )
    lua.execute("""
        engine.work_calls=0; engine.tips={}; engine.objects={}
        local original=function(self,...)
            engine.work_calls=engine.work_calls+1; return 'native',...
        end
        ui_workshop={UIWorkshopRepair={Repair=original},UIWorkshopUpgrade={Upgrade=original},
            UIWorkshopCraft={Craft=original}}
        item_repair={UIRepair={OnRepair=original}}
        ui_inventory={UIInventory={RMode_RepairYes=original,RMode_UpgradeYes=original}}
        news_manager={send_tip=function(actor,text) engine.tips[#engine.tips+1]=text end}
    """)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    engine.files[INCOMING] = encode_incoming(KEY, items, configuration.digest)
    game.actor_on_update()
    return game, engine, configuration


def state_of(lua, game):
    return saved_state(lua, game).gamma_archipelago_v1


def craft_dialog(lua, tier):
    return lua.table(last_type=1, last_index=1, recipes=lua.table(lua.table(lua.table(tool=tier))))


def poll(game, engine):
    engine.now += 1000
    game.actor_on_update()


def test_three_receipts_unlock_tiers_and_reload_derives_permissions_without_spawning(lua):
    game, engine, _ = tool_game(lua, (TOOLS,) * 4)
    module = lua.globals().gamma_ap_workshop
    api = lua.globals().ui_workshop
    assert module.tools_level(state_of(lua, game)) == 1
    assert api.UIWorkshopRepair.Repair(lua.table()) == "native"
    assert api.UIWorkshopCraft.Craft(craft_dialog(lua, 1)) == "native"
    assert api.UIWorkshopCraft.Craft(craft_dialog(lua, 2)) is False
    assert api.UIWorkshopUpgrade.Upgrade(lua.table()) is False
    before = saved_state(lua, game)
    poll(game, engine)
    assert module.tools_level(state_of(lua, game)) == 2
    assert api.UIWorkshopCraft.Craft(craft_dialog(lua, 2)) == "native"
    poll(game, engine)
    assert api.UIWorkshopUpgrade.Upgrade(lua.table()) == "native"
    assert lua.globals().ui_inventory.UIInventory.RMode_UpgradeYes(lua.table()) == "native"
    assert lua.globals().item_repair.UIRepair.OnRepair(lua.table()) == "native"
    assert lua.globals().ui_inventory.UIInventory.RMode_RepairYes(lua.table()) == "native"
    poll(game, engine)
    assert module.tools_level(state_of(lua, game)) == 3
    game.load_state(before)
    assert module.tools_level(state_of(lua, game)) == 1
    assert api.UIWorkshopUpgrade.Upgrade(lua.table()) is False
    poll(game, engine)
    assert module.tools_level(state_of(lua, game)) == 2
    assert not list(engine.created.values())
    upgrades = [
        row for row in game.tracker_view().rows.values() if row.category == "checks_gear_upgrades"
    ]
    assert upgrades and all(row.status == "blocked" for row in upgrades)
    assert (
        sum(row == "Progressive tools: 2/3" for row in game.tracker_view().progression.values())
        == 1
    )


def test_permission_guards_stop_mutation_and_all_actions_delegate_when_disabled(lua):
    game, engine, _ = tool_game(lua)
    api = lua.globals().ui_workshop
    assert api.UIWorkshopRepair.Repair(lua.table()) is False
    assert engine.work_calls == 0 and "Basic" in engine.tips[1]
    assert api.UIWorkshopCraft.Craft(craft_dialog(lua, 4)) == "native"
    assert api.UIWorkshopCraft.Craft(craft_dialog(lua, 6)) == "native"
    for dialog in (
        lua.table(),
        craft_dialog(lua, 0),
        craft_dialog(lua, 7),
        craft_dialog(lua, 1.5),
        craft_dialog(lua, "1"),
        lua.table(recipes=7, last_type=1),
    ):
        assert api.UIWorkshopCraft.Craft(dialog) is False
    state = state_of(lua, game)
    module = lua.globals().gamma_ap_workshop
    state.refused_save = True
    assert module.allowed(state, "repair", lua.table())[0] is False
    state.refused_save = False
    state.session_key = None
    assert module.allowed(state, "repair", lua.table())[0] is False
    state.configuration.options.rewards_progressive_tools = 0
    assert module.allowed(state, "repair", lua.table()) is True
    state.configuration.expanded = False
    assert module.allowed(state, "repair", lua.table()) is True
    state.configuration = None
    assert module.allowed(state, "repair", lua.table()) is True
    assert module.install(None, None) is True


def test_missing_apis_refuse_before_receipt_and_rewrapping_composes(lua):
    game, engine, _ = tool_game(lua)
    api = lua.globals().ui_workshop
    module = lua.globals().gamma_ap_workshop
    saved = state_of(lua, game)
    getter = lua.eval("function(state) return function() return state end end")(saved)
    original = api.UIWorkshopCraft.Craft
    assert module.install(saved.configuration, getter) is True
    lua.execute("""
        local previous=ui_workshop.UIWorkshopCraft.Craft
        ui_workshop.UIWorkshopCraft.Craft=function(...) return previous(...) end
    """)
    assert module.install(saved.configuration, getter) is True
    assert api.UIWorkshopCraft.Craft(craft_dialog(lua, 4)) == "native"
    api.UIWorkshopCraft.Craft = None
    assert module.install(saved.configuration, getter)[0] is False
    api.UIWorkshopCraft.Craft = original
    lua.globals().ui_workshop = None
    assert module.install(saved.configuration, getter)[0] is False
    poll(game, engine)
    assert "workshop" in game.tracker_view().problem


def test_old_default_seed_keeps_workshop_unrestricted(lua):
    game, engine, _ = tool_game(lua)
    state = state_of(lua, game)
    state.configuration.options.rewards_progressive_tools = None
    game.load_state(lua.table(gamma_archipelago_v1=state))
    assert lua.globals().ui_workshop.UIWorkshopRepair.Repair(lua.table()) == "native"


@pytest.mark.parametrize("tier", [1, 2, 3, 4, 5, 6])
def test_crafting_permission_matches_selected_recipe_tool_and_caps_at_expert(lua, tier):
    game, _, _ = tool_game(lua)
    state = state_of(lua, game)
    module = lua.globals().gamma_ap_workshop
    for received in range(5):
        state.applied_items = lua.table_from([TOOLS] * received)
        result = module.allowed(state, "craft", craft_dialog(lua, tier))
        assert (result is True) == (tier > 3 or received >= tier)
