import pytest

from .test_game_adapter import saved_state
from .test_stashes import poll, progress, stash_game


def test_new_stash_doubles_frozen_loot_and_pays_only_when_its_item_is_taken(lua):
    game, engine = stash_game(lua, randomized_stash_loot=1)
    poll(game, engine)
    state = progress(lua, game)
    record = state.stashes.records[1]
    old = lua.globals().gamma_ap_stash_loot.sections(state.session_key, record.item_id, 1, 1)
    base = sum(record.loot_value.prices[section] for section in old.values())
    total = sum(record.loot_value.prices[action.section] for action in record.actions.values())
    assert total >= base * 2
    assert [action.section for action in record.actions.values()][: len(old)] == list(old.values())
    assert (
        record.loot_version == 1 and record.loot_value.version == 1 and record.cash_amount == 5000
    )
    box = engine.boxes[record.cache_id]
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    assert engine.money == 1000
    action = progress(lua, game).stashes.records[1].actions[1]
    lua.globals().test_item = lua.table(
        id=lambda *_: action.created_id,
        name=lambda *_: action.created_name,
        section=lambda *_: action.section,
    )
    game.actor_on_item_take(lua.globals().test_item)
    assert engine.money == 6000
    game.actor_on_item_take(lua.globals().test_item)
    assert engine.money == 6000
    game.load_state(saved_state(lua, game))
    poll(game, engine)
    assert engine.money == 6000
    engine.money = 100
    poll(game, engine)
    assert engine.money == 100  # Spending the payout never creates an entitlement again.


def test_unclaimed_old_stash_upgrades_without_losing_created_item_identities(lua):
    game, engine = stash_game(lua)
    poll(game, engine)
    saved = saved_state(lua, game)
    state = saved.gamma_archipelago_v1
    record = state.stashes.records[1]
    original = lua.globals().gamma_ap_stash_loot.sections(
        state.session_key, record.item_id, 1, None
    )
    record.actions = lua.table_from([lua.table(section=section) for section in original.values()])
    record.loot_version = record.cash_amount = record.cash_target = record.cash_paid = (
        record.loot_value
    ) = None
    record.actions[1].created_id, record.actions[1].created_name = 345, "original"
    record.next_action = 2
    game.load_state(saved)
    poll(game, engine)
    upgraded = progress(lua, game).stashes.records[1]
    assert upgraded.actions[1].created_id == 345
    assert len(upgraded.actions) == len(original) * 2 and upgraded.next_action == 2
    assert upgraded.cash_amount == 5000 and engine.money == 1000


@pytest.mark.parametrize("failure", ["before", "after", "ignored"])
def test_cash_failure_retries_the_absolute_target_without_double_payment(lua, failure):
    _, engine = stash_game(lua)
    record = lua.table(claimed=True, cash_amount=5000, cash_paid=False, loot_version=3)
    lua.globals().failure = failure
    lua.execute("""
        db.actor.give_money=function(self,amount)
            if failure=='before' then error('before') end
            if failure~='ignored' then engine.money=engine.money+amount end
            if failure=='after' then error('after') end
        end
    """)
    module = lua.globals().gamma_ap_stash_rewards
    assert module.pay(record)[0] is False
    assert record.cash_target == 6000 and not record.cash_paid
    lua.globals().failure = "none"
    assert module.pay(record) is True
    assert engine.money == 6000 and record.cash_paid
    assert module.pay(record) is True and engine.money == 6000


@pytest.mark.parametrize("value", [-1, 0.5, "bad", 2147483648])
def test_invalid_native_balance_does_not_latch_or_grant_money(lua, value):
    _, engine = stash_game(lua)
    engine.money = value
    record = lua.table(claimed=True, cash_amount=5000, cash_paid=False)
    assert lua.globals().gamma_ap_stash_rewards.pay(record)[0] is False
    assert record.cash_target is None


def test_cash_cap_remains_pending_until_the_player_has_room_for_the_whole_payout(lua):
    _, engine = stash_game(lua)
    engine.money = 2147483647
    record = lua.table(claimed=True, cash_amount=5000, cash_paid=False)
    module = lua.globals().gamma_ap_stash_rewards
    assert module.pay(record)[0] is False and record.cash_target is None
    engine.money = 1000
    assert module.pay(record) is True and engine.money == 6000


def test_value_bonus_is_varied_and_uses_frozen_prices_instead_of_duplicating_a_quest_item(lua):
    item = 28051201
    game, engine = stash_game(lua, items=(item,), rewards_progression_stashes=1)
    lua.globals().make_cache(30, "esc_treasure_3", "l01_escape", 65535, "invbox")
    engine.prices = lua.table_from({"good_psy_helmet": 0, "medkit_scientic": 2300, "morphine": 700})
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    sections = [action.section for action in record.actions.values()]
    assert sections.count("good_psy_helmet") == 1
    assert sum(record.loot_value.prices[section] for section in sections) >= 5000
    saved = saved_state(lua, game)
    engine.prices = lua.table_from({"good_psy_helmet": 100000, "morphine": 1})
    game.load_state(saved)
    poll(game, engine)
    restored = progress(lua, game).stashes.records[1]
    assert [action.section for action in restored.actions.values()] == sections
    assert restored.loot_value.prices.good_psy_helmet == 0


@pytest.mark.parametrize("price", [-1, 0.5, "bad", 100000001])
def test_invalid_native_price_keeps_reward_pending_without_spawning(lua, price):
    game, engine = stash_game(lua)
    lua.globals().test_price = price
    lua.execute("ini_sys.r_u32=function() return test_price end")
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    assert engine.spawn_calls == 0


def test_impossible_value_budget_is_refused_instead_of_underpaying(lua):
    module = lua.globals().gamma_ap_stash_loot
    key, item = "a" * 64, 28051201
    approved = module.price_sections(key, item, 1, None)
    prices = {section: 1 for section in approved.values()}
    prices["good_psy_helmet"] = 100000000
    value = lua.table(version=1, prices=lua.table_from(prices))
    assert module.sections(key, item, 1, None, value) is None
    prices["good_psy_helmet"] = 0
    prices.update(dict.fromkeys([section for section in prices if section != "good_psy_helmet"], 0))
    assert (
        module.sections(key, item, 1, None, lua.table(version=1, prices=lua.table_from(prices)))
        is None
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"cash_amount": 4999},
        {"cash_paid": 1},
        {"loot_value": None},
        {"cash_target": 0},
        {"cash_target": 1.5},
        {"cash_target": 2147483648},
        {"cash_paid": True},
        {"cash_paid": True, "cash_target": 6000, "claimed": False},
    ],
)
def test_invalid_saved_cash_plan_is_rejected(lua, changes):
    record = lua.table_from(
        dict(
            claimed=True,
            loot_value=lua.table(version=1, prices=lua.table()),
            cash_amount=5000,
            cash_paid=False,
        )
        | changes
    )
    assert lua.globals().gamma_ap_stash_rewards.valid(record) is False
