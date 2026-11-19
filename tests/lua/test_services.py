import pytest

from gamma_archipelago.configuration import encode_configuration

from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, KEY, configured_game
from .test_tracker import state_for


def setup_services(lua):
    lua.execute("""
        db={actor={id=function() return 0 end}}
        shop_name='esc_m_trader'
        mob_trade={GetTalkingNpc=function() return {id=function() return 1 end} end}
        get_object_story_id=function() return shop_name end
        goodwill=0; hostile=false
        relation_registry={community_goodwill=function() return goodwill end}
        game_relations={is_factions_enemies=function() return hostile end}
        character_community=function() return 'stalker' end
    """)


def test_only_one_paid_purchase_at_a_named_trader_counts(lua):
    setup_services(lua)
    module = lua.globals().gamma_ap_services
    state = state_for(lua, checks_shops=1)
    item = lua.table()
    assert module.traded(state, item, False, 100) is True
    assert state.checks[28052901]
    module.traded(state, item, False, 100)
    assert len(list(state.checks.keys())) == 1
    for story in ("bar_visitors_barman_stalker_trader", "yan_stalker_sakharov"):
        lua.globals().shop_name = story
        module.traded(state, item, False, 100)
    assert len(list(state.checks.keys())) == 3
    lua.globals().shop_name = "random_npc"
    module.traded(state, item, False, 100)
    assert len(list(state.checks.keys())) == 3
    lua.globals().mob_trade = None
    assert module.traded(state, item, False, 100)[0] is False
    assert module.traded(state_for(lua), item, False, 100) is True


@pytest.mark.parametrize(
    ("item", "sold", "money"),
    [
        (None, False, 100),
        (True, True, 100),
        (True, None, 100),
        (True, False, 0),
        (True, False, -1),
        (True, False, "100"),
        (True, False, 1.2),
        (True, False, float("nan")),
        (True, False, 2**31),
    ],
)
def test_sales_free_transfers_and_invalid_engine_values_do_not_give_checks(lua, item, sold, money):
    setup_services(lua)
    state = state_for(lua, checks_shops=1)
    lua.globals().gamma_ap_services.traded(state, item, sold, money)
    assert not list(state.checks.keys())


def test_non_hostile_standing_thresholds_are_monotonic_and_api_failures_explicit(lua):
    setup_services(lua)
    module = lua.globals().gamma_ap_services
    state = state_for(lua, checks_faction_standing=1)
    assert module.poll(state_for(lua)) is True
    lua.globals().goodwill = 2000
    assert module.poll(state) is True
    assert set(state.checks.keys()) == {28052911, 28052912, 28052913}
    lua.globals().goodwill = 0
    assert module.poll(state) is True
    assert len(list(state.checks.keys())) == 3
    lua.globals().goodwill = 3000
    lua.globals().hostile = True
    module.poll(state)
    assert not state.checks[28052914]
    lua.globals().hostile = False
    module.poll(state)
    assert state.checks[28052914]
    for bad in ("invalid", 0.5, float("nan"), 2**32):
        lua.globals().goodwill = bad
        assert module.poll(state)[0] is False
    lua.globals().hostile = None
    assert module.poll(state)[0] is False


def test_game_trade_callback_is_additive_and_does_not_grant_an_item(lua):
    game, engine, configuration = configured_game(lua, checks_shops=1)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    game.actor_on_update()
    setup_services(lua)
    game.actor_on_trade(lua.table(), False, 100)
    assert saved_state(lua, game).gamma_archipelago_v1.checks[28052901]
    lua.globals().mob_trade = None
    game.actor_on_trade(lua.table(), False, 100)
    assert "trader" in list(engine.logs.values())[-1]


def test_game_reports_an_unavailable_standing_adapter_before_claiming_checks(lua):
    game, engine, configuration = configured_game(lua, checks_faction_standing=1)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    game.actor_on_update()
    assert "Faction-standing" in list(engine.logs.values())[-1]
    assert not saved_state(lua, game).gamma_archipelago_v1.checks[28052911]
