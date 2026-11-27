from .test_game_adapter import saved_state
from .test_stashes import poll, progress, stash_game


def floor_game(lua):
    game, engine = stash_game(
        lua,
        items=(28051307,) * 5,
        rewards_faction_reputation=1,
        checks_settlements=1,
    )
    lua.execute("""engine.goodwill=-3000;engine.sets=0
        relation_registry={community_goodwill=function(faction,id)
            assert(faction=='army' and id==0);return engine.goodwill end,
            community_relation=function() return -2000 end,
            set_community_goodwill=function(_,_,value)
                engine.sets=engine.sets+1
                if not engine.ignore_set then engine.goodwill=value end
                if engine.throw_after then error('after set') end
            end}
        character_community=function() return 'actor_stalker' end""")
    return game, engine


def test_five_rewards_guarantee_neutrality_despite_prior_debt_then_restore_later_losses_offline(
    lua,
):
    game, engine = floor_game(lua)
    for expected in range(1, 6):
        poll(game, engine)
        assert progress(lua, game).received_count == expected
        assert engine.goodwill >= expected * 250
    assert engine.goodwill == 1250
    game.load_state(saved_state(lua, game))
    engine.goodwill = -3000
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = None
    poll(game, engine)
    assert engine.goodwill == 1250 and progress(lua, game).received_count == 5
    name = "esc_smart_terrain_3_16"
    from .test_settlements import smart

    engine.goodwill = -1000
    game.actor_on_interaction("smarts", smart(lua, name), name)
    assert engine.goodwill == -1000  # Entry does not query or restore reputation.
    assert progress(lua, game).checks[28052103]
    poll(game, engine)
    assert engine.goodwill == 1250  # The independent bounded update still restores the floor.


def test_floor_setter_failure_after_mutation_retries_one_target_without_extra_receipts(lua):
    game, engine = floor_game(lua)
    engine.throw_after = True
    poll(game, engine)
    assert engine.goodwill == 250 and progress(lua, game).received_count == 0
    engine.throw_after = False
    poll(game, engine)
    assert engine.goodwill == 250 and progress(lua, game).received_count == 1
    engine.ignore_set = True
    engine.goodwill = -3000
    poll(game, engine)
    assert progress(lua, game).received_count == 1
    assert "not confirmed" in game.tracker_view().problem
    engine.ignore_set = False
    poll(game, engine)
    assert progress(lua, game).received_count == 2
