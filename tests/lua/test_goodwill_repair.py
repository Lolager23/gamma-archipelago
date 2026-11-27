import pytest

from gamma_archipelago.protocol import encode_incoming

from .test_game_adapter import enter_world, saved_state
from .test_goodwill_migration import PATH, request, setup
from .test_loadout import KEY
from .test_shared_goodwill import setup as shared_setup
from .test_stashes import poll, progress

HOSTILE = ("killer", "army", "bandit")
FRIENDLY = ("stalker", "csky", "dolg", "freedom", "ecolog")


def migrated(lua):
    game, engine, state = setup(lua)
    assert lua.globals().gamma_ap_goodwill_migration.poll(state) is True
    # These are the native results of nine inappropriate shared credits plus
    # genuine dedicated AP rewards. Natural history is intentionally unknown.
    state.applied_items = lua.table_from([28051301] * 3 + [28051306, 28051307, 28051308])
    state.received_count = 6
    for faction in HOSTILE:
        engine.goodwill[faction] = 2500
    return game, engine, state


def test_ap_only_repair_preserves_dedicated_rewards_history_and_limits_future_shared_grants(lua):
    game, engine, state = migrated(lua)
    module = lua.globals().gamma_ap_goodwill_repair
    before = list(state.applied_items.values())
    assert module.ap_only(state, "CONFIRM_AP_ONLY")[0] is True
    assert all(engine.goodwill[faction] == 2500 for faction in HOSTILE)
    assert module.poll(state) is True
    assert all(engine.goodwill[faction] == 250 for faction in HOSTILE)
    assert list(state.applied_items.values()) == before and state.received_count == 6
    assert "Repair completed" in module.report(state)
    assert module.validate(state)
    saved = saved_state(lua, game)
    saved.gamma_archipelago_v1 = state
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = encode_incoming(
        KEY, tuple(before) + (28051301, 28051307), state.configuration_key
    )
    game.load_state(saved)
    enter_world(engine)
    poll(game, engine)
    poll(game, engine)
    state = progress(lua, game)
    assert state.received_count == 8 and state.goodwill_repair.completed
    assert engine.goodwill.army == 500
    assert engine.goodwill.bandit == 250 and engine.goodwill.killer == 250
    assert all(engine.goodwill[faction] == 1000 for faction in FRIENDLY)
    assert "Allied Factions" in lua.globals().gamma_ap_notice_text.render(
        lua.table(kind="received_unlock", local_item_id=28051301, item="old", player="Owen"),
        "allied",
    )
    assert module.ap_only(state, "CONFIRM_AP_ONLY")[0] is False


def test_repair_requires_explicit_consent_and_can_preserve_known_natural_standings(lua):
    _, engine, state = migrated(lua)
    module = lua.globals().gamma_ap_goodwill_repair
    assert module.ap_only(state, "yes")[0] is False
    assert module.prepare(state, 600, 800, 500, "yes")[0] is False
    assert module.prepare(state, 0, 800, 500, "CONFIRM")[0] is False
    assert state.goodwill_repair is None
    assert module.prepare(state, 600, 800, 500, "CONFIRM")[0] is True
    assert module.poll(state) is True
    assert [engine.goodwill[faction] for faction in HOSTILE] == [600, 800, 500]


def test_partial_native_failure_retries_saved_absolute_targets_without_subtracting_twice(lua):
    game, engine, state = migrated(lua)
    module = lua.globals().gamma_ap_goodwill_repair
    assert module.ap_only(state, "CONFIRM_AP_ONLY")[0] is True
    engine.fail_faction = "army"
    assert module.poll(state)[0] is False
    assert (
        engine.goodwill.killer == 250
        and engine.goodwill.army == 250
        and engine.goodwill.bandit == 2500
    )
    saved = saved_state(lua, game)
    saved.gamma_archipelago_v1 = state
    clone = module.copy(state.goodwill_repair)
    clone.targets.army = 999
    assert state.goodwill_repair.targets.army == 250
    assert module.validate(state)
    game.load_state(saved)
    engine.fail_faction = None
    enter_world(engine)
    repaired = progress(lua, game)
    assert module.poll(repaired) is True
    assert all(engine.goodwill[faction] == 250 for faction in HOSTILE)
    assert module.poll(repaired) is True


def test_repair_waits_for_world_and_refuses_to_overwrite_later_unrelated_standing_changes(lua):
    _, engine, state = migrated(lua)
    module = lua.globals().gamma_ap_goodwill_repair
    assert module.ap_only(state, "CONFIRM_AP_ONLY")[0] is True
    lua.globals().gamma_ap_readiness.reset()
    assert "ready world" in module.poll(state)[1]
    enter_world(engine)
    engine.goodwill.army = 2600
    assert "changed since" in module.poll(state)[1]
    assert engine.goodwill.army == 2600


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", 2),
        ("session", "bad"),
        ("configuration", "bad"),
        ("basis", 999),
        ("completed", 1),
        ("targets", {}),
        ("before", {}),
        ("applied", {}),
    ],
)
def test_invalid_saved_repair_is_rejected_before_copy(lua, field, value):
    _, _, state = migrated(lua)
    module = lua.globals().gamma_ap_goodwill_repair
    module.ap_only(state, "CONFIRM_AP_ONLY")
    state.goodwill_repair[field] = lua.table_from(value) if isinstance(value, dict) else value
    assert module.validate(state) is False


def test_fresh_allied_migration_excludes_hostile_standings_and_keeps_legacy_v1_readable(lua):
    _, engine, state = setup(lua)
    module = lua.globals().gamma_ap_goodwill_migration
    engine.files[PATH] = (
        request(state).replace("MIGRATION|1", "MIGRATION|2").replace("end|1", "scope|allied\nend|1")
    )
    assert module.poll(state) is True
    assert state.goodwill_migration.scope == "allied"
    assert set(state.goodwill_migration.targets) == set(FRIENDLY) - {"stalker"}
    assert all(engine.goodwill[faction] is None for faction in HOSTILE)
    assert module.validate(state)
    assert "four allied" in module.message(3, "allied")


def test_public_manual_commands_delegate_to_central_saved_plan_and_report(lua):
    game, engine, state = migrated(lua)
    saved = saved_state(lua, game)
    saved.gamma_archipelago_v1 = state
    game.load_state(saved)
    enter_world(engine)
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = encode_incoming(
        KEY, tuple(state.applied_items.values()), state.configuration_key
    )
    assert game.goodwill_report()[0] is True
    assert game.repair_goodwill(600, 800, 500, "CONFIRM")[0] is True
    poll(game, engine)
    assert progress(lua, game).goodwill_repair.completed
    assert game.repair_goodwill_ap_only("CONFIRM_AP_ONLY")[0] is False
    assert game.goodwill_report()[0] is True


def test_unmigrated_or_wrong_configuration_cannot_be_repaired(lua):
    game, _, state = setup(lua)
    module = lua.globals().gamma_ap_goodwill_repair
    assert module.copy(None) is None and module.validate(state)
    assert module.report(state)[0] is None
    assert module.prepare(state, 0, 0, 0, "CONFIRM")[0] is False
    assert module.ap_only(state, "CONFIRM_AP_ONLY")[0] is False
    assert module.poll(state) is True
    assert game.goodwill_report()[0] is False


def test_new_allied_receipt_only_changes_friendly_factions_and_preserves_partial_plans(lua):
    game, engine = shared_setup(lua, shared_faction_goodwill=2)
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = encode_incoming(
        KEY, (28051310, 28051310), engine.configuration_key
    )
    engine.fail_faction = "dolg"
    poll(game, engine)
    state = progress(lua, game)
    assert state.received_count == 0
    assert set(state.reputation_targets[1]) == set(FRIENDLY)
    assert lua.globals().gamma_ap_reputation.validate_targets(state)
    game.load_state(saved_state(lua, game))
    engine.fail_faction = None
    enter_world(engine)
    poll(game, engine)
    poll(game, engine)
    state = progress(lua, game)
    assert state.received_count == 2
    assert all(engine.goodwill[faction] == 500 for faction in FRIENDLY)
    assert all(engine.goodwill[faction] is None for faction in HOSTILE)
    assert "goodwill rewards 0 / 5" in lua.globals().gamma_ap_settlement_access.reason(
        state, 28052103
    )
    state.reputation_targets[1].army = 500
    assert lua.globals().gamma_ap_reputation.validate_targets(state) is False


@pytest.mark.parametrize("field,value", [("targets", 0), ("before", True), ("applied", 7)])
def test_non_table_repair_data_is_refused(lua, field, value):
    _, _, state = migrated(lua)
    module = lua.globals().gamma_ap_goodwill_repair
    module.ap_only(state, "CONFIRM_AP_ONLY")
    state.goodwill_repair[field] = value
    assert module.validate(state) is False


def test_invalid_targets_changed_standing_and_unavailable_native_apis_do_not_mutate(lua):
    _, engine, state = migrated(lua)
    module = lua.globals().gamma_ap_goodwill_repair
    engine.bad_faction = "army"
    assert module.report(state)[0] is None
    assert module.prepare(state, 250, 250, 250, "CONFIRM")[0] is False
    assert state.goodwill_repair is None
    engine.bad_faction = None
    module.ap_only(state, "CONFIRM_AP_ONLY")
    state.goodwill_repair.targets.army = 0
    assert module.validate(state) is False
    state.goodwill_repair.targets.army = 250
    state.goodwill_repair.applied.army = "yes"
    assert module.validate(state) is False
    state.goodwill_repair.applied.army = False
    state.goodwill_repair.completed = True
    assert module.validate(state) is False
    state.goodwill_repair.completed = False
    engine.bad_faction = "army"
    assert module.poll(state)[0] is False


def test_damaged_migration_cannot_make_repair_validation_throw(lua):
    _, _, state = migrated(lua)
    module = lua.globals().gamma_ap_goodwill_repair
    module.ap_only(state, "CONFIRM_AP_ONLY")
    state.goodwill_migration = 7
    assert module.validate(state) is False


def test_known_negative_standing_is_valid_when_no_dedicated_ap_floor_was_earned(lua):
    _, engine, state = migrated(lua)
    state.applied_items = lua.table_from([28051301] * 3)
    state.received_count = 3
    module = lua.globals().gamma_ap_goodwill_repair
    assert module.prepare(state, -200, -300, -500, "CONFIRM")[0] is True
    assert module.validate(state)
    assert module.poll(state) is True
    assert [engine.goodwill[faction] for faction in HOSTILE] == [-200, -300, -500]
    assert lua.globals().gamma_ap_reputation.reconcile(state) is True
    assert [engine.goodwill[faction] for faction in HOSTILE] == [-200, -300, -500]
