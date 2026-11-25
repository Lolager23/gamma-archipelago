"""GAMMA's custom UI reports actor_on_item_buy, not the engine trade callback."""

import pytest

from gamma_archipelago.configuration import encode_configuration

from .test_loadout import CONFIG_PATH, KEY, configured_game
from .test_services import setup_services
from .test_shop_purchases import OFFER, buy, shop_game
from .test_stashes import poll, progress
from .test_tracker import state_for


def custom_shop(lua):
    game, engine, configuration = configured_game(lua, checks_shops=1, checks_maps=0)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    game.on_game_start()
    engine.creation.new_game_faction = None
    poll(game, engine)
    lua.execute("""
        engine.money=1000
        engine.partner={id=function() return 11 end}
        engine.story_ids[11]='esc_m_trader'
        mob_trade=nil
        native_buy=function(price)
            if engine.money<math.floor(price) then return false end
            engine.callbacks.actor_on_item_buy({},price,engine.partner)
            engine.money=engine.money-math.floor(price)
            return 'bought',nil,3
        end
    """)
    return game, engine


@pytest.mark.parametrize(
    "story,identifier",
    [
        ("esc_m_trader", 28052901),
        ("bar_visitors_barman_stalker_trader", 28052902),
        ("yan_stalker_sakharov", 28052903),
    ],
)
@pytest.mark.parametrize("price", [1, 100, 100.75])
def test_registered_custom_ui_callback_records_named_paid_purchases_without_legacy_callback(
    lua, story, identifier, price
):
    game, engine = custom_shop(lua)
    engine.story_ids[11] = story
    assert lua.globals().native_buy(price) == ("bought", None, 3)
    assert progress(lua, game).checks[identifier]
    lua.execute("mob_trade={GetTalkingNpc=function() error('must not resolve talking NPC') end}")
    lua.globals().native_buy(price)
    assert len(list(progress(lua, game).checks.keys())) == 1


@pytest.mark.parametrize("price", [None, "100", -1, 0, 0.75, float("nan"), float("inf"), 2**31])
def test_free_invalid_and_sub_ruble_events_do_not_count(lua, price):
    game, engine = custom_shop(lua)
    engine.callbacks.actor_on_item_buy(lua.table(), price, engine.partner)
    assert not list(progress(lua, game).checks.keys())


def test_unaffordable_purchase_sales_and_dedicated_ap_contracts_do_not_count(lua):
    game, _ = custom_shop(lua)
    assert lua.globals().native_buy(2000) is False
    setup_services(lua)
    game.actor_on_trade(lua.table(), True, 100)
    assert not list(progress(lua, game).checks.keys())
    game, _ = shop_game(lua, checks_shops=1)
    assert buy(game)[0]
    checks = progress(lua, game).checks
    assert checks[OFFER] and not any(checks[id_] for id_ in (28052901, 28052902, 28052903))


@pytest.mark.parametrize(
    "change",
    [
        "state.session_key=nil",
        "state.refused_save=true",
        "state.expanded=false",
        "state.configuration=nil",
        "state.configuration.expanded=false",
        "state.configuration.options.checks_shops=0",
        "state.enabled_checks[28052901]=nil",
    ],
)
def test_unbound_refused_disabled_or_unconfigured_events_cannot_change_checks(lua, change):
    lua.globals().state = state_for(lua, checks_shops=1)
    lua.execute(change)
    lua.execute(
        "npc={id=function() return 11 end}; "
        "get_object_story_id=function() return 'esc_m_trader' end"
    )
    module = lua.globals().gamma_ap_services
    assert module.bought(lua.globals().state, lua.table(), 100.5, lua.globals().npc) is True
    assert not list(lua.globals().state.checks.keys())


def test_unknown_missing_or_unsupported_trader_never_records_a_different_shop(lua):
    game, engine = custom_shop(lua)
    engine.story_ids[11] = "random_npc"
    engine.callbacks.actor_on_item_buy(lua.table(), 100, engine.partner)
    engine.callbacks.actor_on_item_buy(lua.table(), 100, None)
    engine.callbacks.actor_on_item_buy(None, 100, engine.partner)
    assert not list(progress(lua, game).checks.keys())
    lua.execute("engine.partner.id=function() error('unsupported partner') end")
    engine.callbacks.actor_on_item_buy(lua.table(), 100, engine.partner)
    assert "named trader" in list(engine.logs.values())[-1]


def test_legacy_and_custom_callbacks_share_one_saved_monotonic_check(lua):
    game, _ = custom_shop(lua)
    lua.globals().native_buy(100.5)
    setup_services(lua)
    game.actor_on_trade(lua.table(), False, 100)
    assert list(progress(lua, game).checks.keys()) == [28052901]
    snapshot = lua.table()
    game.save_state(snapshot)
    game.load_state(snapshot)
    game.actor_on_item_buy(lua.table(), 100.5, lua.table(id=lua.eval("function() return 1 end")))
    assert list(progress(lua, game).checks.keys()) == [28052901]
