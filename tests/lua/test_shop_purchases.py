import pytest

from gamma_archipelago.catalog import ALL_LOCATION_IDS
from gamma_archipelago.configuration import encode_configuration
from gamma_archipelago.protocol import decode_outgoing, encode_confirmed, encode_incoming

from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, KEY, configured_game
from .test_stashes import poll, progress

OFFER = 28052921
ROOT = "D:/AnomalyAP/appdata/archipelago\\"


def shop_game(lua, **options):
    game, engine, config = configured_game(lua, checks_shop_purchases=1, **options)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, config, expanded=True)
    poll(game, engine)
    lua.execute("""
        engine.money=25000; engine.debits=0; engine.partner_id=1; engine.story='esc_m_trader'
        engine.shown=true; engine.mode='trade'
        db.actor.id=function() return 0 end
        engine.partner={id=function() return engine.partner_id end}
        ui_inventory=ui_inventory or {}
        ui_inventory.GUI={IsShown=function() return engine.shown end,
            mode=engine.mode,GetPartner=function() return engine.partner end}
        get_object_story_id=function() return engine.story end
        db.actor.money=function()
            if engine.fail_read or (engine.fail_after_read and engine.debits>0) then
                error('wallet read failed')
            end
            return engine.money
        end
        db.actor.give_money=function(self,amount)
            engine.debits=engine.debits+1
            if engine.raise_before then error('debit failed') end
            if not engine.ignore_debit then
                engine.money=engine.money+amount+(engine.debit_offset or 0)
            end
            if engine.raise_after then error('debit completed then callback failed') end
        end
    """)
    return game, engine


def buy(game, identity=OFFER, key=KEY, npc=1):
    return game.buy_shop_check(identity, key, npc)


def test_named_offer_debits_exact_price_and_queues_one_check_without_a_world_update(lua):
    game, engine = shop_game(lua)
    rows = list(game.shop_view().rows.values())
    assert [row.id for row in rows] == [OFFER, OFFER + 1, OFFER + 2]
    assert [row.price for row in rows] == [2500, 7500, 15000]
    assert all(row.name and row.description and not row.completed for row in rows)
    assert buy(game)[0]
    assert engine.money == 22500 and engine.debits == 1
    packet = decode_outgoing(
        engine.files[ROOT + "outgoing.txt"],
        KEY,
        ALL_LOCATION_IDS,
        configuration_key=progress(lua, game).configuration_key,
    )
    assert OFFER in packet.checked_locations
    assert not buy(game)[0]
    assert engine.debits == 1
    assert game.shop_view().rows[1].completed
    game.load_state(saved_state(lua, game))
    assert not buy(game)[0] and engine.debits == 1


def test_each_merchant_has_three_distinct_finite_offers_and_all_nine_can_be_bought(lua):
    game, engine = shop_game(lua)
    engine.money = 75000
    for shop, first in (
        ("esc_m_trader", OFFER),
        ("bar_visitors_barman_stalker_trader", OFFER + 3),
        ("yan_stalker_sakharov", OFFER + 6),
    ):
        engine.story = shop
        engine.level = {
            "esc_m_trader": "l01_escape",
            "bar_visitors_barman_stalker_trader": "l05_bar",
            "yan_stalker_sakharov": "l08_yantar",
        }[shop]
        assert [row.id for row in game.shop_view().rows.values()] == list(range(first, first + 3))
        for identity in range(first, first + 3):
            assert buy(game, identity)[0]
    assert engine.money == 0 and engine.debits == 9
    assert set(progress(lua, game).checks.keys()) >= set(range(OFFER, OFFER + 9))


@pytest.mark.parametrize(
    "change", ["npc", "shop", "id", "key", "hidden", "mode", "dead", "refused", "disabled"]
)
def test_wrong_context_session_or_disabled_check_never_spends_money(lua, change):
    game, engine = shop_game(lua)
    identity, key, npc = OFFER, KEY, 1
    if change == "npc":
        npc = 2
    elif change == "shop":
        engine.story = "yan_stalker_sakharov"
    elif change == "id":
        identity = 28052901
    elif change == "key":
        key = "b" * 64
    elif change == "hidden":
        engine.shown = False
    elif change == "mode":
        lua.globals().ui_inventory.GUI.mode = "repair"
    elif change == "dead":
        engine.alive = False
    else:
        saved = saved_state(lua, game)
        state = saved.gamma_archipelago_v1
        if change == "refused":
            state.schema_version = 999
        else:
            state.configuration.options.checks_shop_purchases = 0
        game.load_state(saved)
    assert buy(game, identity, key, npc)[0] is False
    assert engine.debits == 0 and engine.money == 25000


@pytest.mark.parametrize("money", [2499, -1, 1.5, "25000", float("nan"), 2**31])
def test_insufficient_or_invalid_wallet_is_not_debited(lua, money):
    game, engine = shop_game(lua)
    engine.money = money
    assert buy(game)[0] is False and engine.debits == 0


@pytest.mark.parametrize("failure", ["ignore_debit", "raise_before"])
def test_proven_unpaid_failure_can_retry_without_charging_twice(lua, failure):
    game, engine = shop_game(lua)
    engine[failure] = True
    assert not buy(game)[0]
    assert not progress(lua, game).shop_payments[OFFER]
    assert not progress(lua, game).checks[OFFER]
    engine[failure] = False
    assert buy(game)[0] and engine.money == 22500


def test_a_callback_exception_after_a_proven_debit_still_completes_the_paid_check(lua):
    game, engine = shop_game(lua)
    engine.raise_after = True
    assert buy(game)[0]
    assert engine.money == 22500 and progress(lua, game).checks[OFFER]


@pytest.mark.parametrize("failure", ["fail_after_read", "debit_offset"])
def test_uncertain_payment_is_saved_and_never_automatically_charged_again(lua, failure):
    game, engine = shop_game(lua)
    engine[failure] = 1
    assert not buy(game)[0]
    saved = saved_state(lua, game)
    assert saved.gamma_archipelago_v1.shop_payments[OFFER].balance_before == 25000
    engine[failure] = False if failure == "fail_after_read" else 0
    game.load_state(saved)
    assert not buy(game)[0] and engine.debits == 1
    assert game.shop_view().rows[1].uncertain
    assert not progress(lua, game).checks[OFFER]
    engine.files[ROOT + "confirmed_checks.txt"] = encode_confirmed(KEY, frozenset({OFFER}))
    assert not buy(game)[0]
    assert progress(lua, game).checks[OFFER]
    assert not progress(lua, game).shop_payments[OFFER]


def test_older_save_with_a_server_confirmed_purchase_is_not_charged_again(lua):
    game, engine = shop_game(lua)
    old = saved_state(lua, game)
    assert buy(game)[0]
    game.load_state(old)
    engine.money = 25000
    engine.files[ROOT + "confirmed_checks.txt"] = encode_confirmed(KEY, frozenset({OFFER}))
    assert not buy(game)[0]
    assert engine.money == 25000 and engine.debits == 1


def test_offline_write_failure_retains_purchase_and_does_not_repeat_payment(lua):
    game, engine = shop_game(lua)
    engine.fail_write = True
    paid, message = buy(game)
    assert paid and "saved locally" in message
    assert engine.debits == 1
    engine.fail_write = False
    poll(game, engine)
    assert (
        OFFER
        in decode_outgoing(
            engine.files[ROOT + "outgoing.txt"],
            KEY,
            ALL_LOCATION_IDS,
            configuration_key=progress(lua, game).configuration_key,
        ).checked_locations
    )
    assert not buy(game)[0] and engine.debits == 1


def test_changed_or_partial_bridge_and_invalid_confirmations_prevent_payment(lua):
    game, engine = shop_game(lua)
    incoming = engine.files[ROOT + "incoming.txt"]
    for content in ("partial", encode_incoming("b" * 64, ()), encode_incoming(KEY, (), "b" * 64)):
        engine.files[ROOT + "incoming.txt"] = content
        assert not buy(game)[0]
    engine.files[ROOT + "incoming.txt"] = incoming
    engine.files[ROOT + "confirmed_checks.txt"] = "partial"
    assert not buy(game)[0] and engine.debits == 0


@pytest.mark.parametrize("problem", ["missing_ui", "missing_partner", "bad_story", "wallet"])
def test_unavailable_native_context_returns_an_empty_view(lua, problem):
    game, engine = shop_game(lua)
    if problem == "missing_ui":
        lua.globals().ui_inventory = None
    elif problem == "missing_partner":
        engine.partner = None
    elif problem == "bad_story":
        engine.story = "random_stalker"
    else:
        engine.fail_read = True
    assert len(game.shop_view().rows) == 0
    assert not buy(game)[0] and engine.debits == 0


@pytest.mark.parametrize(
    "mutation",
    [
        "state.shop_payments=false",
        "state.shop_payments={[42]={}}",
        "state.shop_payments={[28052921]=false}",
        "state.shop_payments={[28052921]={price=1,balance_before=5000}}",
        "state.shop_payments={[28052921]={price=2500,balance_before=1}}",
        "state.shop_payments={[28052921]={price=2500,balance_before=3000}};state.session_key=nil",
        "state.shop_payments={[28052921]={price=2500,balance_before=3000}};state.configuration=nil",
        "state.shop_payments={[28052921]={price=2500,balance_before=3000}};state.configuration.options.checks_shop_purchases=0",
    ],
)
def test_malformed_payment_journals_are_refused_before_save_load_mutation(lua, mutation):
    game, _ = shop_game(lua)
    saved = saved_state(lua, game)
    lua.globals().state = saved.gamma_archipelago_v1
    lua.execute(mutation)
    game.load_state(saved)
    assert progress(lua, game).refused_save


def test_legacy_save_without_payment_field_migrates_and_uncertain_copy_is_detached(lua):
    game, _ = shop_game(lua)
    saved = saved_state(lua, game)
    saved.gamma_archipelago_v1.shop_payments = None
    game.load_state(saved)
    assert len(progress(lua, game).shop_payments) == 0
    module = lua.globals().gamma_ap_shop
    value = lua.table_from({OFFER: lua.table(price=2500, balance_before=5000)})
    cloned = module.copy(value)
    cloned[OFFER].price = 7500
    assert value[OFFER].price == 2500


@pytest.mark.parametrize("content", [None, "partial"])
def test_missing_or_partial_configuration_cannot_charge_from_a_stale_shop_view(lua, content):
    game, engine = shop_game(lua)
    engine.files[CONFIG_PATH] = content
    assert not buy(game)[0] and engine.debits == 0


def test_receipt_history_conflicts_prevent_payment_and_disabled_shop_categories_stay_hidden(lua):
    game, engine = shop_game(lua)
    digest = progress(lua, game).configuration_key
    engine.files[ROOT + "incoming.txt"] = encode_incoming(KEY, (), digest)
    assert not buy(game)[0]
    engine.files[ROOT + "incoming.txt"] = encode_incoming(KEY, (28051001,), digest)
    assert not buy(game)[0] and engine.debits == 0
    game, engine = shop_game(lua, optional_check_policy=1)
    assert len(game.shop_view().rows) == 0
    assert not buy(game)[0] and engine.debits == 0


@pytest.mark.parametrize("identity", [0, 65535, 1.5, float("nan")])
def test_invalid_native_trader_identity_cannot_expose_a_purchase(lua, identity):
    game, engine = shop_game(lua)
    engine.partner_id = identity
    assert len(game.shop_view().rows) == 0
    assert not buy(game)[0] and engine.debits == 0


@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("new_logic", [0, 1])
def test_shop_reward_details_respect_the_seed_scouting_option(lua, mode, new_logic):
    game, _ = shop_game(lua, scouting_mode=mode, playability_logic=new_logic)
    lua.execute("""
        scout_reads=0
        gamma_ap_scouting.view=function()
            scout_reads=scout_reads+1
            return {rewards={[28052921]={item='Foreign Key',player='Friend'}}}
        end
    """)
    row = game.shop_view().rows[1]
    assert lua.globals().scout_reads == (1 if mode or new_logic else 0)
    assert (row.reward is not None) == bool(mode or new_logic)
    if mode or new_logic:
        assert row.reward.item == "Foreign Key" and row.reward.player == "Friend"


def test_trader_region_and_zone_permissions_match_ap_world_access(lua):
    from .test_tracker import state_for

    _, engine = shop_game(lua)
    state = state_for(lua, checks_shop_purchases=1, rewards_zone_keys=1)
    module = lua.globals().gamma_ap_shop
    engine.story = "bar_visitors_barman_stalker_trader"
    assert len(module.snapshot(state).rows) == 0
    assert not module.purchase(state, OFFER + 3, KEY, 1)[0] and engine.debits == 0
    engine.level = "l05_bar"
    assert len(module.snapshot(state).rows) == 0
    assert "zone access" in module.purchase(state, OFFER + 3, KEY, 1)[1]
    state.unlocks.zone_l05_bar = True
    assert len(module.snapshot(state).rows) == 3
    assert module.purchase(state, OFFER + 3, KEY, 1)[0]
