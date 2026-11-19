from .test_game_adapter import saved_state
from .test_stashes import poll, progress, stash_game


def quest_game(lua, **options):
    game, engine = stash_game(lua, items=(28051501,), rewards_quest_keys=1, **options)
    lua.execute("""
        engine.grants=0; engine.manager={task_info={}}
        task_manager={CRandomTask={give_task=function(self,id,giver)
            engine.grants=engine.grants+1
            if engine.fail_grant then error('grant') end
            if not engine.ignore_grant then self.task_info[id]={giver=giver} end
            return 'native'
        end},get_task_manager=function() return engine.manager end}
    """)
    return game, engine


def test_quest_key_defers_native_assignments_and_replays_once_after_unlock(lua):
    game, engine = quest_game(lua)
    game.on_game_start()
    manager = engine.manager
    api = lua.globals().task_manager.CRandomTask
    assert api.give_task(manager, "lttz_ll_find_doctor", 7) is None
    api.give_task(manager, "lttz_ll_find_doctor", 99)
    assert engine.grants == 0
    game.load_state(lua.table())
    assert progress(lua, game).quest_pending.lttz_ll_find_doctor.giver == 7
    poll(game, engine)
    assert progress(lua, game).unlocks.living_legend
    assert not manager.task_info.lttz_ll_find_doctor
    engine.fail_grant = True
    poll(game, engine)
    assert progress(lua, game).quest_pending.lttz_ll_find_doctor
    engine.fail_grant = False
    engine.ignore_grant = True
    poll(game, engine)
    assert progress(lua, game).quest_pending.lttz_ll_find_doctor
    engine.ignore_grant = False
    game.load_state(saved_state(lua, game))
    poll(game, engine)
    assert manager.task_info.lttz_ll_find_doctor.giver == 7
    assert not progress(lua, game).quest_pending.lttz_ll_find_doctor
    calls = engine.grants
    poll(game, engine)
    assert calls == engine.grants
    assert api.give_task(manager, "ordinary_side_task", 2) == "native"


def test_unavailable_quest_manager_is_visible_and_integration_is_composable(lua):
    game, engine = quest_game(lua)
    poll(game, engine)
    state = progress(lua, game)
    module = lua.globals().gamma_ap_quest_keys
    state.quest_pending.lttz_ll_find_doctor = lua.table(giver=4)
    api = lua.globals().task_manager
    api.get_task_manager = None
    assert module.poll(state)[0] is False
    api.get_task_manager = lua.eval("function() return nil end")
    assert module.poll(state)[0] is False
    api.get_task_manager = lua.eval("function() return engine.manager end")
    engine.manager.task_info.lttz_ll_find_doctor = lua.table(giver=4)
    assert module.poll(state) is True
    # Another mod can wrap our method; captured delegates must not form a cycle.
    lua.execute("""
        local previous=task_manager.CRandomTask.give_task
        task_manager.CRandomTask.give_task=function(...) return previous(...) end
    """)
    assert module.install(lua.eval("function() return gamma_ap_state.new_state() end")) is True
    assert api.CRandomTask.give_task(engine.manager, "ordinary", 8) == "native"
    lua.globals().task_manager = None
    assert module.install(lua.eval("function() return {} end"))[0] is False


def test_missing_grant_hook_refuses_enabled_configuration_before_rewards(lua):
    game, engine = quest_game(lua)
    lua.globals().task_manager = None
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    assert "grant method" in list(engine.logs.values())[-1]
