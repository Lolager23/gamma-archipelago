import pytest

from .test_game_adapter import enter_world, saved_state
from .test_shared_goodwill import FACTIONS
from .test_stashes import poll, progress, stash_game

PATH = "D:/AnomalyAP/appdata/archipelago\\goodwill_migration.txt"


def setup(lua, count=3):
    game, engine = stash_game(
        lua,
        items=(28051301,) * (count + 1),
        rewards_faction_reputation=1,
        shared_faction_goodwill=0,
    )
    lua.execute("""
        engine.goodwill={};engine.sets={}
        relation_registry={community_goodwill=function(faction)
            if engine.bad_faction==faction then error('query') end
            return engine.goodwill[faction] or 0 end,
            set_community_goodwill=function(faction,id,target)
                engine.sets[faction]=(engine.sets[faction] or 0)+1
                if not engine.ignore_set then engine.goodwill[faction]=target end
                if engine.fail_faction==faction then error('after mutation') end
            end}
    """)
    for _ in range(count):
        poll(game, engine)
    state = progress(lua, game)
    engine.files[PATH] = request(state)
    return game, engine, state


def request(state):
    return (
        "GAMMA_AP_GOODWILL_MIGRATION|1\n"
        f"session|{state.session_key}\nconfiguration|{state.configuration_key}\n"
        "convert_loner|1\nend|1\n"
    )


def test_backfill_preserves_ids_checks_and_existing_loner_standing_then_upgrades_future_rewards(
    lua,
):
    game, engine, state = setup(lua)
    state.checks[28052001] = True
    before = list(state.applied_items.values())
    module = lua.globals().gamma_ap_goodwill_migration
    assert module.poll(state) is True
    assert all(engine.goodwill[faction] == 750 for faction in FACTIONS)
    assert list(state.applied_items.values()) == before
    assert state.received_count == 3 and state.checks[28052001]
    assert module.notice(state) is True
    assert len(engine.stash_news) == 1
    assert module.poll(state) is True and len(engine.stash_news) == 1
    # Bind this detached migrated save into the coordinator and deliver the next old ID.
    saved = saved_state(lua, game)
    saved.gamma_archipelago_v1 = state
    game.load_state(saved)
    enter_world(engine)
    poll(game, engine)
    assert progress(lua, game).received_count == 4
    assert list(progress(lua, game).applied_items.values()) == [28051301] * 4
    assert all(engine.goodwill[faction] == 1000 for faction in FACTIONS)
    game.load_state(saved_state(lua, game))
    enter_world(engine)
    poll(game, engine)
    assert all(engine.goodwill[faction] == 1000 for faction in FACTIONS)


def test_partial_backfill_retry_survives_save_load_and_retains_absolute_targets(lua):
    game, engine, state = setup(lua)
    engine.goodwill.army = 3500
    engine.fail_faction = "dolg"
    module = lua.globals().gamma_ap_goodwill_migration
    assert module.poll(state)[0] is False
    assert engine.goodwill.dolg == 750 and state.goodwill_migration.completed is False
    saved = saved_state(lua, game)
    saved.gamma_archipelago_v1 = state
    game.load_state(saved)
    engine.fail_faction = None
    enter_world(engine)
    poll(game, engine)
    assert progress(lua, game).received_count == 4
    assert engine.goodwill.dolg == 1000 and engine.goodwill.army == 3500
    assert progress(lua, game).goodwill_migration.completed
    assert engine.sets.dolg == 2  # One backfill and one future reward, not a repeated backfill.


def test_migration_waits_for_loading_and_plans_before_mutating_any_faction(lua):
    game, engine, state = setup(lua)
    game.load_state(saved_state(lua, game))
    module = lua.globals().gamma_ap_goodwill_migration
    assert "ready world" in module.poll(state)[1]
    enter_world(engine)
    engine.bad_faction = "bandit"
    before = dict(engine.sets)
    assert module.poll(state)[0] is False
    assert dict(engine.sets) == before and state.goodwill_migration is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: s[:-1],
        lambda s: "x" * 513,
        lambda s: s.replace("|1\n", "|2\n", 1),
        lambda s: s.replace("session|", "session|a"),
        lambda s: s.replace("configuration|", "configuration|a"),
    ],
)
def test_malformed_migration_request_never_changes_native_standing(lua, mutate):
    _, engine, state = setup(lua)
    engine.files[PATH] = mutate(request(state))
    before = dict(engine.goodwill)
    assert lua.globals().gamma_ap_goodwill_migration.poll(state)[0] is False
    assert dict(engine.goodwill) == before and state.goodwill_migration is None


def test_other_session_request_and_read_failure_are_refused(lua):
    _, engine, state = setup(lua)
    module = lua.globals().gamma_ap_goodwill_migration
    engine.files[PATH] = request(state).replace(state.session_key, "c" * 64)
    assert "another seed" in module.poll(state)[1]
    engine.files[PATH] = request(state)
    engine.fail_close = True
    assert "read failed" in module.poll(state)[1]


def test_pending_legacy_loner_target_is_not_granted_twice_when_converted(lua):
    game, engine, state = setup(lua)
    state.reputation_targets[4] = 1000
    engine.goodwill.stalker = 1000  # Setter succeeded before the old receipt was acknowledged.
    module = lua.globals().gamma_ap_goodwill_migration
    assert module.poll(state) is True
    saved = saved_state(lua, game)
    saved.gamma_archipelago_v1 = state
    game.load_state(saved)
    enter_world(engine)
    poll(game, engine)
    assert progress(lua, game).received_count == 4
    assert all(engine.goodwill[faction] == 1000 for faction in FACTIONS)


def test_migration_notice_failure_cannot_block_a_later_item_receipt(lua):
    game, engine, state = setup(lua)
    assert lua.globals().gamma_ap_goodwill_migration.poll(state) is True
    saved = saved_state(lua, game)
    saved.gamma_archipelago_v1 = state
    game.load_state(saved)
    enter_world(engine)
    engine.fail_stash_notice = True
    poll(game, engine)
    assert progress(lua, game).received_count == 4
    assert progress(lua, game).goodwill_migration.notice_pending
    engine.fail_stash_notice = False
    poll(game, engine)
    assert all(engine.goodwill[faction] == 1000 for faction in FACTIONS)
    assert len(engine.stash_news) == 1


def test_migration_sentence_has_translation_ready_english_fallback(lua):
    module = lua.globals().gamma_ap_goodwill_migration
    assert "factions: 3." in module.message(3)
    lua.execute("game={translate_string=function() return 'Upgraded {count} rewards' end}")
    assert module.message(3) == "Upgraded 3 rewards"
    lua.execute("game.translate_string=function() return '<bad> {count}' end")
    assert "factions: 3." in module.message(3)


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", 2),
        ("count", 4),
        ("basis", 4),
        ("completed", 1),
        ("notice_pending", 1),
        ("session", "bad"),
        ("configuration", "bad"),
        ("targets", {}),
    ],
)
def test_damaged_migration_plans_are_rejected_before_state_copy(lua, field, value):
    _, _, state = setup(lua)
    module = lua.globals().gamma_ap_goodwill_migration
    assert module.poll(state) is True
    state.goodwill_migration[field] = lua.table_from(value) if isinstance(value, dict) else value
    assert module.validate(state) is False
