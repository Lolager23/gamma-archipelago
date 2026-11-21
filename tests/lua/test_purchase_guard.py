import pytest

from .test_gear_locks import gear_game
from .test_stashes import poll, progress


def shop(lua, *, psi_guard=False):
    game, engine = gear_game(lua, items=(), psi_guard=psi_guard)
    poll(game, engine)
    lua.globals().state = progress(lua, game)
    lua.execute("""
        engine.native_buys=0;engine.warnings={}
        ui_inventory={UIInventory={TMode_Buy=function(self,...)
            engine.native_buys=engine.native_buys+1;engine.money=engine.money-500
            return 'bought',nil,3
        end}}
        game={translate_string=function(key) return key end}
        window={CC={npc_trade={indx_id={[50]=1}}},message_box={
            InitMessageBox=function() end,SetText=function(self,text) self.text=text end,
            ShowDialog=function(self) engine.warnings[#engine.warnings+1]=self.text end}}
        gamma_ap_purchase_guard.install(function() return state end)
    """)
    return lua.globals().gamma_ap_purchase_guard, engine


def test_passive_psi_device_still_cannot_bypass_progression_stash_permission(lua):
    _, engine = shop(lua, psi_guard=True)
    lua.globals().add_item(50, "good_psy_helmet", "II_ATTCH", "i_quest", 0)
    assert lua.globals().ui_inventory.UIInventory.TMode_Buy(lua.globals().window) is False
    assert engine.money == 1000 and engine.native_buys == 0
    assert list(engine.warnings.values()) == ["gamma_ap_purchase_locked"]


@pytest.mark.parametrize(
    "change",
    [
        "state.unlocks.gear_pda=true",
        "state.configuration=nil",
        "state.configuration.expanded=false",
        "window.CC=nil",
    ],
)
def test_permitted_and_unconfigured_baskets_preserve_native_return_values(lua, change):
    _, engine = shop(lua)
    lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    lua.execute(change)
    assert lua.globals().ui_inventory.UIInventory.TMode_Buy(lua.globals().window) == (
        "bought",
        None,
        3,
    )
    assert engine.money == 500 and engine.native_buys == 1


def test_disappeared_item_blocks_whole_basket_and_wrapper_is_idempotent(lua):
    module, engine = shop(lua)
    getter = lua.eval("function() return state end")
    assert module.install(getter) is True
    assert lua.globals().ui_inventory.UIInventory.TMode_Buy(lua.globals().window) is False
    assert engine.money == 1000 and engine.warnings[1] == "gamma_ap_purchase_unavailable"
    lua.globals().ui_inventory = None
    assert module.install(getter) is False
    lua.globals().ui_inventory = lua.table(UIInventory=lua.table())
    assert module.install(getter) is False


def test_basket_with_unrestricted_supplies_uses_normal_trade(lua):
    _, engine = shop(lua)
    lua.globals().add_item(50, "bandage", "II_BANDG", "i_medical", 0)
    lua.globals().ui_inventory.UIInventory.TMode_Buy(lua.globals().window)
    assert engine.native_buys == 1 and not len(engine.warnings)


def test_locked_equipment_uses_normal_trade_without_losing_money_or_items(lua):
    _, engine = shop(lua)
    item = lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    lua.globals().ui_inventory.UIInventory.TMode_Buy(lua.globals().window)
    assert engine.money == 500 and engine.native_buys == 1 and not len(engine.warnings)
    lua.globals().engine.callbacks.actor_on_item_take(item)
    assert engine.objects[50] and not engine.dropped[50]
