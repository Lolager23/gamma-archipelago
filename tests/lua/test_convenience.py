import pytest

from .test_workshop import poll, state_of, tool_game

CARRY = 28051911


def carry_game(lua, items=(CARRY,) * 4):
    game, engine, configuration = tool_game(
        lua, items, rewards_progressive_tools=0, rewards_convenience=1
    )
    assert state_of(lua, game).received_count == 0
    lua.execute("""
        engine.weights={other=7}; engine.weight_calls=0
        weight={add_weight=function(key,amount,force)
            assert(force==true)
            engine.weight_calls=engine.weight_calls+1; engine.weights[key]=amount
            if engine.weight_error then error('after keyed mutation') end
            return not engine.weight_refuse
        end,remove_weight=function(key) engine.weights[key]=nil end}
    """)
    return game, engine, configuration


def test_carry_bonus_is_additive_capped_and_does_not_accumulate_on_repeated_polls(lua):
    game, engine, _ = carry_game(lua)
    for amount in (5, 10, 15, 15):
        poll(game, engine)
        assert engine.weights.gamma_archipelago_carry == amount
        assert engine.weights.other == 7
    calls = engine.weight_calls
    poll(game, engine)
    assert engine.weight_calls == calls
    assert state_of(lua, game).received_count == 4
    assert any("+15 kg" in text for text in game.tracker_view().progression.values())
    assert not list(engine.created.values())


def test_rollback_disabled_refused_and_new_actor_reconcile_only_the_owned_key(lua):
    game, engine, _ = carry_game(lua)
    poll(game, engine)
    saved = state_of(lua, game)
    poll(game, engine)
    module = lua.globals().gamma_ap_convenience
    assert module.poll(saved) is True
    assert engine.weights.gamma_archipelago_carry == 5
    calls = engine.weight_calls
    lua.execute("db.actor={}")
    assert module.poll(saved) is True and engine.weight_calls == calls + 1
    saved.refused_save = True
    assert module.poll(saved) is True and engine.weights.gamma_archipelago_carry is None
    assert engine.weights.other == 7
    saved.refused_save = False
    assert module.poll(saved) is True
    saved.configuration.options.rewards_convenience = 0
    assert module.poll(saved) is True and engine.weights.gamma_archipelago_carry is None
    saved.configuration = None
    assert module.poll(saved) is True


@pytest.mark.parametrize("failure", ["weight_error", "weight_refuse"])
def test_keyed_effect_failure_can_retry_without_growth_or_receipt_acknowledgement(lua, failure):
    game, engine, _ = carry_game(lua)
    engine[failure] = True
    poll(game, engine)
    assert state_of(lua, game).received_count == 0
    assert engine.weights.gamma_archipelago_carry == 5
    assert "receipt remains pending" in game.tracker_view().problem
    engine[failure] = False
    poll(game, engine)
    assert state_of(lua, game).received_count == 1
    assert engine.weights.gamma_archipelago_carry == 5 and engine.weights.other == 7


def test_invalid_reward_unsupported_api_and_unbound_state_do_not_acknowledge(lua):
    game, engine, _ = carry_game(lua)
    module = lua.globals().gamma_ap_convenience
    state = state_of(lua, game)
    assert module.receive(state, 28051001)[0] is False
    lua.globals().weight.add_weight = None
    assert module.receive(state, CARRY)[0] is False
    state.session_key = None
    assert module.receive(state, CARRY)[0] is False
    state.session_key = "a" * 64
    state.configuration.options.rewards_convenience = 0
    assert module.receive(state, CARRY)[0] is False
    state.configuration = None
    assert module.receive(state, CARRY)[0] is False
    assert state_of(lua, game).received_count == 0
