import pytest

from .test_pda_ui import load_ui, panel_text
from .test_shop_purchases import shop_game


def trader_ui(lua):
    game, engine = shop_game(lua)
    load_ui(lua, xml_filename="gamma_ap_shop.xml", strings_filename="st_gamma_ap_shop.xml")
    lua.globals().gamma_ap_game = game
    lua.execute("""
        native_calls={reset=0,trade=0,update=0}
        ui_inventory.UIInventory={
            Reset=function(self,npc)
                native_calls.reset=native_calls.reset+1; self.npc_id=npc and npc:id()
                return 'reset',nil,'preserved'
            end,
            TMode_Init=function(self,npc)
                native_calls.trade=native_calls.trade+1; self.mode='trade'; self:Reset(npc)
                return 'trade',42
            end,
            Update=function(self)
                native_calls.update=native_calls.update+1; return 'update',nil,17
            end,
        }
        window=CUIWindow(); window.x=0; window.y=0
        window.npc_dialog=CUIWindow(); window.npc_dialog.x=0; window.npc_dialog.y=0
        window.npc_dialog:SetWndSize(vector2():set(377,768))
        window.npc_trade=CUIWindow()
        window.CC={npc_trade=CUIWindow(),npc_trade_bag=CUIWindow()}
        window.GetPartner=function() return engine.partner end
        window.On_Item_Update=function()
            engine.inventory_updates=(engine.inventory_updates or 0)+1
        end
        ui_inventory.GUI=window
    """)
    module = lua.globals().gamma_ap_shop_ui
    assert module.install(lua.table(expanded=True, options=lua.table(checks_shop_purchases=1)))
    lua.execute("""
        for name,method in pairs(ui_inventory.UIInventory) do window[name]=method end
        window:TMode_Init(engine.partner)
    """)
    return game, engine, module, lua.globals().window


def toggle(window):
    window.callbacks.gamma_ap_shop_toggle()


def test_docked_shop_button_opens_descriptive_offers_and_restores_native_goods(lua):
    _, _, _, window = trader_ui(lua)
    ui = window.gamma_ap_shop
    assert ui.button.IsShown(ui.button)
    assert not ui.panel.IsShown(ui.panel)
    assert ui.button.width == 114 and ui.button.x + ui.button.width < 140
    toggle(window)
    assert ui.panel.IsShown(ui.panel) and ui.open
    assert not window.npc_trade.IsShown(window.npc_trade)
    for row in ui.rows.values():
        content = panel_text(row.info)
        assert "Contract" in content and "Sidorovich" in content and "Purchase the" in content
        assert "Assigned reward is hidden" in content
        assert row.buy.IsEnabled(row.buy)
        assert row.icon.width == 38
    toggle(window)
    assert window.npc_trade.IsShown(window.npc_trade)
    assert window.CC.npc_trade_bag.IsShown(window.CC.npc_trade_bag)


def test_row_purchase_uses_its_own_check_id_and_immediately_updates_money_and_status(lua):
    game, engine, _, window = trader_ui(lua)
    toggle(window)
    window.callbacks.gamma_ap_shop_buy_2()
    assert engine.money == 17500 and engine.inventory_updates == 1
    assert game.shop_view().rows[2].completed
    assert not game.shop_view().rows[1].completed
    ui = window.gamma_ap_shop
    assert ui.rows[2].buy.TextControl(ui.rows[2].buy).text == "Purchased"
    assert not ui.rows[2].buy.IsEnabled(ui.rows[2].buy)
    window.callbacks.gamma_ap_shop_buy_2()
    assert engine.debits == 1


def test_update_preserves_native_returns_and_bounds_metadata_refresh_with_an_explicit_clock(lua):
    game, engine, _, window = trader_ui(lua)
    lua.globals().shop_view_delegate = game.shop_view
    lua.execute("""
        view_calls=0
        gamma_ap_game.shop_view=function() view_calls=view_calls+1; return shop_view_delegate() end
    """)
    toggle(window)
    count = lua.globals().view_calls
    for _ in range(20):
        assert window.Update(window) == ("update", None, 17)
    assert lua.globals().view_calls == count
    engine.money = 1000
    window.Update(window)
    assert not window.gamma_ap_shop.rows[1].buy.IsEnabled(window.gamma_ap_shop.rows[1].buy)
    assert "1000" in window.gamma_ap_shop.balance.text
    assert lua.globals().view_calls == count
    lua.globals().clock += 500
    window.Update(window)
    assert lua.globals().view_calls == count + 1
    lua.globals().clock = 1
    window.Update(window)
    assert lua.globals().view_calls == count + 2


def test_paid_and_uncertain_rows_are_disabled_and_native_reset_rebinds_the_page(lua):
    _, engine, _, window = trader_ui(lua)
    toggle(window)
    engine.debit_offset = 1
    window.callbacks.gamma_ap_shop_buy_1()
    assert (
        window.gamma_ap_shop.rows[1].buy.TextControl(window.gamma_ap_shop.rows[1].buy).text
        == "Payment needs review"
    )
    assert not window.gamma_ap_shop.rows[1].buy.IsEnabled(window.gamma_ap_shop.rows[1].buy)
    engine.story = "yan_stalker_sakharov"
    engine.level = "l08_yantar"
    assert window.Reset(window, engine.partner) == ("reset", None, "preserved")
    assert not window.gamma_ap_shop.open
    assert not window.gamma_ap_shop.panel.IsShown(window.gamma_ap_shop.panel)
    toggle(window)
    assert "Sakharov" in panel_text(window.gamma_ap_shop.rows[1].info)


def test_hidden_or_disabled_seed_restores_stock_and_does_not_hijack_other_modes(lua):
    _, engine, module, window = trader_ui(lua)
    toggle(window)
    window.mode = "repair"
    module.refresh(window)
    assert not window.gamma_ap_shop.panel.IsShown(window.gamma_ap_shop.panel)
    assert not window.gamma_ap_shop.button.IsShown(window.gamma_ap_shop.button)
    assert not window.gamma_ap_shop.open
    window.mode = "trade"
    engine.story = "random_stalker"
    module.refresh(window)
    assert not window.gamma_ap_shop.button.IsShown(window.gamma_ap_shop.button)


def test_long_reward_names_scroll_without_covering_buy_buttons_and_survive_gc(lua):
    _, _, module, window = trader_ui(lua)
    view = lua.globals().gamma_ap_game.shop_view()
    view.rows[1].reward = lua.table(item="Very long reward " * 20, player="Long recipient " * 20)
    lua.globals().gamma_ap_game = lua.table(shop_view=lambda: view)
    toggle(window)
    ui = window.gamma_ap_shop
    info = ui.rows[1].info
    assert info["items"][1].height > info.height
    assert info.y + info.height < ui.rows[1].buy.y
    assert ui.rows[3].parent.y + ui.rows[3].parent.height < ui.footer.y
    count = info.cleared
    info.position = 100
    module.refresh(window)
    assert info.cleared == count and info.position == 100
    lua.execute("collectgarbage('collect'); CUIScriptWnd.Update(window.npc_dialog)")
    assert "Very long reward" in panel_text(info)


def test_installer_is_idempotent_disabled_is_a_noop_and_rewrapped_native_hooks_delegate(lua):
    _, _, module, window = trader_ui(lua)
    config = lua.table(expanded=True, options=lua.table(checks_shop_purchases=1))
    original = lua.globals().ui_inventory.UIInventory.Update
    module.install(config)
    lua.globals().first_wrapper = original
    assert lua.eval("ui_inventory.UIInventory.Update==first_wrapper")
    assert module.install(None)
    assert module.install(lua.table(expanded=False))
    lua.execute("ui_inventory.UIInventory.Update=function() return 'new native' end")
    assert module.install(config)
    assert lua.globals().ui_inventory.UIInventory.Update(window) == "new native"


def test_partial_offer_views_hide_the_unused_card_and_pass_native_boolean_flags(lua):
    game, _, module, window = trader_ui(lua)
    view = game.shop_view()
    view.rows[3] = None
    lua.globals().gamma_ap_game = lua.table(shop_view=lambda: view)
    toggle(window)
    window.Update(window)
    assert not window.gamma_ap_shop.rows[3].parent.IsShown(window.gamma_ap_shop.rows[3].parent)
    assert not window.gamma_ap_shop.rows[3].buy.IsEnabled(window.gamma_ap_shop.rows[3].buy)
    module.refresh(window)


def test_missing_translations_use_short_fallbacks_and_losing_the_trader_restores_stock(lua):
    _, engine, module, window = trader_ui(lua)
    lua.globals().translations = lua.table()
    module.refresh(window)
    assert window.gamma_ap_shop.button.TextControl(window.gamma_ap_shop.button).text == "AP shop"
    toggle(window)
    assert "Sidorovich" in panel_text(window.gamma_ap_shop.rows[1].info)
    engine.story = "random_stalker"
    module.refresh(window)
    assert window.npc_trade.IsShown(window.npc_trade)
    assert not window.gamma_ap_shop.panel.IsShown(window.gamma_ap_shop.panel)


def test_wallet_read_failure_disables_purchase_without_polling_files_per_frame(lua):
    _, engine, _, window = trader_ui(lua)
    toggle(window)
    engine.fail_read = True
    window.Update(window)
    assert all(not row.buy.IsEnabled(row.buy) for row in window.gamma_ap_shop.rows.values())


def test_unsupported_window_layout_keeps_native_trade_and_logs_a_bounded_diagnostic(lua):
    _, engine, _, _ = trader_ui(lua)
    before = len(engine.logs)
    lua.execute("""
        bad_window=CUIWindow()
        for name,method in pairs(ui_inventory.UIInventory) do bad_window[name]=method end
        ui_inventory.GUI=bad_window
        bad_window:TMode_Init(engine.partner)
        bad_window:TMode_Init(engine.partner)
    """)
    assert len(engine.logs) == before + 1
    assert "Unsupported trader layout" in list(engine.logs.values())[-1]
    assert lua.globals().bad_window.gamma_ap_shop is None


@pytest.mark.parametrize("missing", ["UIInventory", "TMode_Init", "Reset", "Update"])
def test_unsupported_native_inventory_fails_explicitly_without_partial_hooking(lua, missing):
    lua.execute(
        "ui_inventory={UIInventory={TMode_Init=function() end,"
        "Reset=function() end,Update=function() end}}"
    )
    target = lua.globals().ui_inventory
    if missing == "UIInventory":
        target.UIInventory = None
    else:
        target.UIInventory[missing] = None
    result = lua.globals().gamma_ap_shop_ui.install(
        lua.table(expanded=True, options=lua.table(checks_shop_purchases=1))
    )
    assert result[0] is False and "supported GAMMA" in result[1]
