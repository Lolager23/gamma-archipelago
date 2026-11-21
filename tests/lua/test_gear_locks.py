import pytest

from .test_game_adapter import saved_state
from .test_stashes import poll, progress, stash_game


def gear_game(lua, *, items=(28051602,), psi_guard=False):
    game, engine = stash_game(
        lua,
        items=items,
        starting_pda=2,
        rewards_starting_gear_unlocks=1,
        rewards_progression_stashes=int(psi_guard),
    )
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


def test_locked_equipment_can_be_carried_but_use_requires_permission(lua):
    game, engine = gear_game(lua, items=())
    poll(game, engine)
    item = lua.globals().add_item(50, "pda", "D_PDA", "i_device", 0)
    flags = lua.table(ret_value=True)
    game.actor_on_item_before_pickup(item, flags)
    assert flags.ret_value is True
    game.actor_on_item_before_use(item, flags)
    assert flags.ret_value is False
    game.actor_on_item_take(item)
    game.actor_on_item_take_from_box(None, item)
    poll(game, engine)
    assert engine.objects[50] and progress(lua, game).received_count == 0
    game.actor_on_item_take_from_box(None, item)
    assert not engine.dropped[50] and engine.objects[50]
    another = lua.globals().add_item(51, "pda", "D_PDA", "i_device", 0)
    game.actor_on_item_take(another)
    assert not engine.dropped[51] and engine.objects[51]
    lua.globals().add_item(52, "pda", "D_PDA", "i_device", 0)
    poll(game, engine)
    assert not engine.dropped[52] and engine.objects[52]


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


@pytest.mark.parametrize("other_veto", [None, "veto_before", "veto_after"])
def test_pickup_veto_does_not_latch_into_later_allowed_items_or_override_current_mod_veto(
    lua, other_veto
):
    game, engine = gear_game(lua, items=(), psi_guard=True)
    poll(game, engine)
    locked = lua.globals().add_item(50, "good_psy_helmet", "II_ATTCH", "i_quest", 0)
    allowed = lua.globals().add_item(51, "bandage", "S_FOOD", "i_medical", 0)
    pickup = lua.globals().bind_stalker_ext.actor_on_item_before_pickup
    assert pickup(locked) is False, list(engine.logs.values())
    if other_veto:
        engine[other_veto] = True
        assert pickup(allowed) is False
        engine[other_veto] = False
    assert pickup(allowed) is True
    assert pickup(locked) is False
    assert pickup(allowed) is True


def test_missing_native_pickup_guard_refuses_psi_locked_seed_before_receipt(lua):
    game, engine = gear_game(lua, psi_guard=True)
    lua.globals().bind_stalker_ext = None
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    assert "pickup binder" in list(engine.logs.values())[-1]


def test_missing_pickup_guard_at_start_can_register_when_the_native_binder_loads(lua):
    game, engine = gear_game(lua, psi_guard=True)
    binder = lua.globals().bind_stalker_ext
    lua.globals().bind_stalker_ext = None
    engine.creation.new_game_faction = "stalker"
    game.on_game_start()
    assert any("pickup binder" in message for message in engine.logs.values())
    lua.globals().bind_stalker_ext = binder
    engine.creation.new_game_faction = None
    poll(game, engine)
    assert progress(lua, game).received_count == 1


def test_pickup_guard_preserves_another_mods_delegating_wrapper(lua):
    game, engine = gear_game(lua, items=(), psi_guard=True)
    poll(game, engine)
    lua.execute("""
        local delegate=bind_stalker_ext.actor_on_item_before_pickup
        engine.pickup_delegations=0
        bind_stalker_ext.actor_on_item_before_pickup=function(...)
            engine.pickup_delegations=engine.pickup_delegations+1
            return delegate(...)
        end
    """)
    poll(game, engine)
    locked = lua.globals().add_item(50, "good_psy_helmet", "II_ATTCH", "i_quest", 0)
    allowed = lua.globals().add_item(51, "bandage", "S_FOOD", "i_medical", 0)
    pickup = lua.globals().bind_stalker_ext.actor_on_item_before_pickup
    assert pickup(locked) is False
    assert pickup(allowed) is True
    assert engine.pickup_delegations == 2


def test_repeated_fresh_sessions_rebind_pickup_guard_without_losing_permissions(lua):
    for _ in range(32):
        game, engine = gear_game(lua, items=(), psi_guard=True)
        poll(game, engine)
        state = progress(lua, game)
        assert state.session_key and state.configuration.options.starting_pda == 2, list(
            engine.logs.values()
        )
        locked = lua.globals().add_item(50, "good_psy_helmet", "II_ATTCH", "i_quest", 0)
        allowed = lua.globals().add_item(51, "bandage", "S_FOOD", "i_medical", 0)
        pickup = lua.globals().bind_stalker_ext.actor_on_item_before_pickup
        assert pickup(locked) is False, list(engine.logs.values())
        assert pickup(allowed) is True
