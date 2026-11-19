import pytest

from .test_game_adapter import load_game, saved_state, set_incoming
from .test_gear_locks import gear_game
from .test_stashes import poll, progress, stash_game


@pytest.mark.parametrize(
    "mutation",
    [
        "state.schema_version=2",
        "state.refused_save=true",
        "state.session_key='wrong'",
        "state.received_count=-1",
        "state.applied_items=nil",
        "state.checks=nil",
        "state.received_count=1;state.applied_items={42}",
        "state.applied_items.extra=28051001",
        "state.checks[42]=true",
        "state.checks[28052001]=false",
        "state.unlocks=7",
        "state.unlocks.unknown=true",
        "state.unlocks.gear_pda='true'",
        "state.stashes=false",
        "state.stashes.order=7",
        "state.any=function() end",
        "state.any=string.rep('x',4097)",
        "state.any=0/0",
        "state.any=state",
        "state[function() end]=1",
        "state.any=setmetatable({}, {})",
        "local t=state;for i=1,18 do t.child={};t=t.child end",
    ],
)
def test_malformed_save_data_is_refused_before_engine_mutation(lua, mutation):
    state = lua.globals().gamma_ap_state.new_state()
    state.session_key = "a" * 64
    lua.globals().state = state
    lua.execute(mutation)
    result = lua.globals().gamma_ap_save_validation.validate(state)
    assert result[0] is False and isinstance(result[1], str)


def test_legacy_plain_save_and_all_check_id_families_remain_valid(lua):
    state = lua.globals().gamma_ap_state.new_state()
    state.schema_version = None
    state.session_key = "a" * 64
    for identity in (28052001, 28052401, 28100001, 28120001):
        state.checks[identity] = True
    state.unlocks.gear_pda = True
    assert lua.globals().gamma_ap_save_validation.validate(state) is True
    module = lua.globals().gamma_ap_save_validation
    module.MAX_ENTRIES = 1
    assert module.validate(state)[0] is False
    assert module.validate(False)[0] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "record.item_id=42",
        "record.cache_name='unknown';record.level=nil",
        "record.cache_id=65535",
        "record.next_action=0",
        "record.actions={}",
        "record.actions[1].section='unapproved_section'",
        "record.actions[1]=7",
        "state.stashes.order={1,1}",
        "state.stashes.records[1]=7",
        "state.stashes.records[2]=record",
        "state.stashes.order={4001}",
    ],
)
def test_saved_stash_plans_cannot_change_approved_contents_or_receipt_bounds(lua, mutation):
    game, engine = stash_game(lua)
    poll(game, engine)
    state = progress(lua, game)
    lua.globals().state = state
    lua.globals().record = state.stashes.records[1]
    lua.execute(mutation)
    assert lua.globals().gamma_ap_save_validation.validate(state)[0] is False


def test_invalid_load_persists_refusal_instead_of_silently_resetting_receipts(lua):
    game, engine = load_game(lua)
    set_incoming(engine)
    game.actor_on_update()
    valid = saved_state(lua, game)
    bad = lua.globals().gamma_ap_state.new_state()
    bad.received_count = "bad"
    game.load_state(lua.table(gamma_archipelago_v1=bad))
    assert progress(lua, game).refused_save
    before = len(engine.created)
    poll(game, engine)
    assert len(engine.created) == before
    game.load_state(saved_state(lua, game))
    assert progress(lua, game).refused_save
    game.load_state(valid)
    assert not progress(lua, game).refused_save
    bad = lua.globals().gamma_ap_state.new_state()
    bad.combat = 7  # Plain data, but incompatible with the owned copy structure.
    game.load_state(lua.table(gamma_archipelago_v1=bad))
    assert progress(lua, game).refused_save


def test_validator_exception_is_contained_without_dropping_into_an_unbound_save(lua):
    game, engine = load_game(lua)
    module = lua.globals().gamma_ap_save_validation
    module.validate = lua.eval("function() error('invalid nested shape') end")
    game.load_state(lua.table(gamma_archipelago_v1=lua.table()))
    assert progress(lua, game).refused_save
    assert "validation failed" in list(engine.logs.values())[-1]


def test_confirmed_creation_markers_resume_without_repeating_physical_side_effects(lua):
    game, engine = stash_game(lua)
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    poll(game, engine)
    saved = saved_state(lua, game)
    saved.gamma_archipelago_v1.stashes.records[1].next_action = 1
    game.load_state(saved)
    calls = engine.spawn_calls
    poll(game, engine)
    assert engine.spawn_calls == calls


def test_baseline_permission_creation_marker_can_finish_its_unacknowledged_receipt(lua):
    game, engine = gear_game(lua)
    poll(game, engine)
    saved = saved_state(lua, game)
    saved.gamma_archipelago_v1.received_count = 0
    saved.gamma_archipelago_v1.applied_items = lua.table()
    game.load_state(saved)
    calls = engine.spawn_calls
    poll(game, engine)
    assert engine.spawn_calls == calls and progress(lua, game).received_count == 1


def test_unbound_progress_and_permissions_cannot_be_attached_to_a_different_seed(lua):
    module = lua.globals().gamma_ap_save_validation
    state = lua.globals().gamma_ap_state.new_state()
    state.goal_complete = True
    assert module.validate(state)[0] is False
    state.goal_complete = False
    state.unlocks.gear_pda = True
    assert module.validate(state)[0] is False
