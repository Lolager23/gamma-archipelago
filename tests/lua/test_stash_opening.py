import pytest

from .test_game_adapter import saved_state
from .test_stashes import ADVANCED, poll, progress, stash_game


def test_loot_is_created_during_use_before_the_loot_ui_without_an_actor_update(lua):
    game, engine = stash_game(lua, items=(ADVANCED,))
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    box = engine.boxes[record.cache_id]
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    # GAMMA rebuilds the loot screen on its next UI frame, not the next AP poll.
    assert engine.spawn_calls == len(record.actions)
    assert all(item.owner == record.cache_id for item in engine.spawns.values())
    filled = progress(lua, game).stashes.records[1]
    assert filled.opened and filled.next_action == len(record.actions) + 1
    assert not filled.claimed
    game.load_state(saved_state(lua, game))
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    assert engine.spawn_calls == len(record.actions)


def test_a_saved_empty_opened_stash_resumes_at_use_without_replaying_its_receipt(lua):
    game, engine = stash_game(lua)
    poll(game, engine)
    saved = saved_state(lua, game)
    record = saved.gamma_archipelago_v1.stashes.records[1]
    record.opened = True  # Legacy save made after opening but before the AP poll.
    game.load_state(saved)
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    assert engine.spawn_calls == len(record.actions)
    assert progress(lua, game).received_count == 1


def test_shared_stash_use_is_bounded_and_reopening_finishes_only_pending_actions(lua):
    game, engine = stash_game(lua, items=(ADVANCED,) * 8)
    # One eligible native box makes the deterministic plans share a container.
    lua.globals().treasure_manager.caches = lua.table_from({1: False})
    for _ in range(8):
        poll(game, engine)
    box = engine.boxes[1]
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    assert engine.spawn_calls == 64
    assert "close and reopen" in list(engine.logs.values())[-1]
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    assert engine.spawn_calls == 72
    assert progress(lua, game).received_count == 8
    assert all(record.next_action == 10 for record in progress(lua, game).stashes.records.values())
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    assert engine.spawn_calls == 72


def test_creation_error_during_use_is_reported_and_a_known_failure_can_retry(lua):
    game, engine = stash_game(lua)
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    engine.fail_spawn = True
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    assert "item creation failed" in list(engine.logs.values())[-1]
    assert progress(lua, game).stashes.records[1].next_action == 1
    engine.fail_spawn = False
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    assert engine.spawn_calls == len(record.actions) + 1


def test_use_without_marker_readiness_does_not_spawn_but_retains_the_plan(lua):
    game, engine = stash_game(lua)
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    lua.globals().modxml_gamma_ap_stashes.ready = lua.eval("function() return false end")
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    assert engine.spawn_calls == 0
    assert progress(lua, game).stashes.records[1].opened
    assert "contents remain pending" in list(engine.logs.values())[-1]
    lua.globals().modxml_gamma_ap_stashes.ready = lua.eval("function() return true end")
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    assert engine.spawn_calls == len(record.actions)


@pytest.mark.parametrize("change", ["parent", "class", "level", "missing"])
def test_use_validates_saved_container_identity_before_mutating_or_creating(lua, change):
    game, engine = stash_game(lua)
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    server = engine.servers[record.cache_id]
    if change == "parent":
        server.parent_id = 0
    elif change == "class":
        server.clsid = lua.eval("function() return 'actor' end")
    elif change == "level":
        server.m_game_vertex_id = "l05_bar"
    else:
        engine.servers[record.cache_id] = None
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    assert not progress(lua, game).stashes.records[1].opened
    assert engine.spawn_calls == 0
    assert "will not reroll" in list(engine.logs.values())[-1]


@pytest.mark.parametrize("change", ["who", "dead", "box", "pda", "refused"])
def test_invalid_or_disallowed_use_cannot_grant_loot(lua, change):
    game, engine = stash_game(lua)
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    box, who = engine.boxes[record.cache_id], lua.globals().db.actor
    if change == "who":
        who = lua.table(id=lua.eval("function() return 99 end"))
    elif change == "dead":
        engine.alive = False
    elif change == "box":
        box = None
    elif change == "pda":
        state = saved_state(lua, game)
        state.gamma_archipelago_v1.starting_pda_mode = 2
        engine.objects = lua.table()
        game.load_state(state)
    else:
        state = saved_state(lua, game)
        state.gamma_archipelago_v1.schema_version = 999
        game.load_state(state)
        assert progress(lua, game).refused_save
    game.physic_object_on_use_callback(box, who)
    assert engine.spawn_calls == 0
