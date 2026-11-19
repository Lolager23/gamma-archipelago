import pytest

from .test_game_adapter import saved_state
from .test_loadout import KEY
from .test_stashes import poll, progress, stash_game


def test_goodwill_reward_is_bounded_personal_saved_and_uses_a_retry_target(lua):
    game, engine = stash_game(lua, items=(28051301, 28051301), rewards_faction_reputation=1)
    lua.execute("""
        engine.goodwill=390; engine.sets=0
        relation_registry={
            community_goodwill=function(faction,id)
                if engine.bad_query then error('query failed') end
                assert(faction=='stalker' and id==0); return engine.goodwill
            end,
            set_community_goodwill=function(faction,id,target)
                engine.sets=engine.sets+1
                if not engine.ignore_set then engine.goodwill=target end
                if engine.throw_after then error('after side effect') end
            end}
    """)
    engine.throw_after = True
    poll(game, engine)
    assert engine.goodwill == 640 and progress(lua, game).received_count == 0
    game.load_state(saved_state(lua, game))
    engine.throw_after = False
    poll(game, engine)
    assert engine.goodwill == 640 and progress(lua, game).received_count == 1
    engine.goodwill = 2990
    poll(game, engine)
    assert engine.goodwill == 3000 and progress(lua, game).received_count == 2
    assert engine.sets == 2


@pytest.mark.parametrize("value", [None, True, 0.5, float("inf"), -2147483649])
def test_invalid_goodwill_values_refuse_mutation(lua, value):
    stash_game(lua)
    module = lua.globals().gamma_ap_reputation
    state = lua.globals().gamma_ap_state.new_state()
    assert module.receive(state, 28051301)[0] is False
    state.session_key, state.expanded = KEY, True
    state.allowed_items[28051301] = True
    assert module.receive(state, 28051301)[0] is False
    lua.globals().relation_registry = lua.table(
        community_goodwill=lua.eval("function() return invalid_value end"),
        set_community_goodwill=lua.eval("function() error('should not set') end"),
    )
    lua.globals().invalid_value = value
    assert module.receive(state, 28051301)[0] is False


def test_unchanged_or_unconfirmed_setters_retry_without_compounding(lua):
    game, engine = stash_game(lua, items=(28051301,), rewards_faction_reputation=1)
    lua.execute("""
        engine.goodwill=0
        relation_registry={community_goodwill=function() return engine.goodwill end,
            set_community_goodwill=function() end}
    """)
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    assert progress(lua, game).reputation_targets[1] == 250
    engine.goodwill = 4000
    poll(game, engine)
    assert progress(lua, game).received_count == 1 and engine.goodwill == 4000


def test_query_exception_is_reported(lua):
    game, engine = stash_game(lua, items=(28051301,), rewards_faction_reputation=1)
    lua.execute(
        """relation_registry={community_goodwill=function() error('query') end,
        set_community_goodwill=function() end}"""
    )
    poll(game, engine)
    assert progress(lua, game).received_count == 0
