import pytest

from .test_game_adapter import saved_state
from .test_stashes import poll, progress, stash_game


def gear_game(lua, *, items=(28051602,)):
    game, engine = stash_game(lua, items=items, starting_pda=2, rewards_starting_gear_unlocks=1)
    lua.execute("""
        engine.dropped={}
        level.object_by_id=function(id) return engine.objects[id] or engine.boxes[id] end
        db.actor.drop_item=function(self,item)
            if engine.fail_drop then error('drop failed') end
            engine.dropped[item:id()]=true; engine.objects[item:id()]=nil
        end
    """)
    game.on_game_start()
    engine.creation.new_game_faction = None
    return game, engine


def test_locked_start_is_omitted_then_permission_grants_usable_baseline(lua):
    game, engine = gear_game(lua)
    assert "pda" not in engine.creation.new_game_loadout
    poll(game, engine)
    assert not engine.objects[2]
    assert progress(lua, game).unlocks.gear_pda
    assert progress(lua, game).received_count == 1
    assert next(iter(engine.spawns.values())).section == "device_pda_1"
    item = lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    flags = lua.table(ret_value=True)
    game.actor_on_item_before_pickup(item, flags)
    assert flags.ret_value
    game.actor_on_item_take(item)
    assert engine.objects[50]
    game.load_state(saved_state(lua, game))
    poll(game, engine)
    assert engine.spawn_calls == 1


def test_locked_sources_are_blocked_or_returned_without_destroying_loot(lua):
    game, engine = gear_game(lua, items=())
    poll(game, engine)
    item = lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    flags = lua.table(ret_value=True)
    game.actor_on_item_before_pickup(item, flags)
    assert flags.ret_value is False
    game.actor_on_item_before_use(item, flags)
    engine.fail_drop = True
    game.actor_on_item_take(item)
    game.actor_on_item_take_from_box(None, item)
    poll(game, engine)
    assert engine.objects[50] and progress(lua, game).received_count == 0
    engine.fail_drop = False
    game.actor_on_item_take_from_box(None, item)
    assert engine.dropped[50]
    another = lua.globals().add_item(51, "pda", "D_PDA", "i_device", 0)
    game.actor_on_item_take(another)
    assert engine.dropped[51]
    lua.globals().add_item(52, "pda", "D_PDA", "i_device", 0)
    poll(game, engine)
    assert engine.dropped[52]


@pytest.mark.parametrize("failure", ["fail_spawn", "raise_spawn", "missing_section"])
def test_failed_baseline_does_not_acknowledge_and_uncertainty_survives_load(lua, failure):
    game, engine = gear_game(lua)
    engine[failure] = "device_pda_1" if failure == "missing_section" else True
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    game.load_state(saved_state(lua, game))
    calls = engine.spawn_calls
    engine[failure] = False
    poll(game, engine)
    if failure == "raise_spawn":
        assert engine.spawn_calls == calls and progress(lua, game).received_count == 0
    else:
        assert progress(lua, game).received_count == 1


def test_unknown_or_unselected_equipment_permissions_refuse_delivery(lua):
    game, engine = gear_game(lua)
    poll(game, engine)
    state = progress(lua, game)
    assert lua.globals().gamma_ap_gear_locks.receive(state, 28051601)[0] is False
    assert lua.globals().gamma_ap_gear_locks.receive(state, 1)[0] is False
