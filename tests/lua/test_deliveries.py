import pytest

from .test_collection import artefact
from .test_workshop import TOOLS, poll, state_of, tool_game


def supply_game(lua, items=(28051811,), **options):
    return tool_game(
        lua,
        items,
        permission_supplies=1,
        rewards_workshop_access=1,
        rewards_recipe_access=1,
        **options,
    )


def test_partial_delivery_saves_cursor_resumes_without_repeating_and_delays_permission(lua):
    game, engine, _ = supply_game(lua)
    state = state_of(lua, game)
    assert list(engine.created.values()) == ["gun_oil"]
    assert state.received_count == 0 and not state.unlocks.workshop_repair
    assert state.deliveries[1].next_action == 2
    assert "1/2 supplies delivered" in game.tracker_view().delivery
    state.deliveries[1].sections[1] = "edited_copy"
    assert state_of(lua, game).deliveries[1].sections[1] == "gun_oil"
    saved = state_of(lua, game)
    game.load_state(lua.table(gamma_archipelago_v1=saved))
    poll(game, engine)
    assert list(engine.created.values()) == ["gun_oil", "glue_a"]
    assert state_of(lua, game).unlocks.workshop_repair and state_of(lua, game).received_count == 1
    assert game.tracker_view().delivery is None
    assert game.tracker_view().problem is None
    poll(game, engine)
    assert list(engine.created.values()) == ["gun_oil", "glue_a"]
    # Older-save rollback replays history using the restored cursor; the engine
    # itself must restore spawned inventory. This does not claim crash-proof delivery.
    game.load_state(lua.table(gamma_archipelago_v1=saved))
    poll(game, engine)
    assert engine.created[3] == "glue_a"


def test_progressive_permission_delivers_one_native_tool_per_tier_and_caps_extra_copies(lua):
    game, engine, _ = supply_game(lua, (TOOLS,) * 4)
    for _ in range(3):
        poll(game, engine)
    assert list(engine.created.values()) == ["itm_basickit", "itm_advancedkit", "itm_expertkit"]
    assert state_of(lua, game).received_count == 4
    assert lua.globals().gamma_ap_workshop.tools_level(state_of(lua, game)) == 3
    assert lua.globals().gamma_ap_deliveries.validate(state_of(lua, game))


def test_duplicate_permanent_permission_does_not_repeat_its_attached_consumables(lua):
    game, engine, _ = supply_game(lua, (28051811, 28051811))
    poll(game, engine)
    poll(game, engine)
    assert state_of(lua, game).received_count == 2
    assert list(engine.created.values()) == ["gun_oil", "glue_a"]


def test_definite_failure_retries_without_advancing_and_all_sections_preflight_before_spawn(lua):
    game, engine, _ = supply_game(lua)
    engine.fail_reward = True
    poll(game, engine)
    state = state_of(lua, game)
    assert state.received_count == 0 and state.deliveries[1].next_action == 2
    assert not state.applying_reward
    engine.fail_reward = False
    engine.missing_section = "glue_a"
    poll(game, engine)
    assert engine.created[2] is None
    engine.missing_section = None
    poll(game, engine)
    assert state_of(lua, game).received_count == 1 and engine.created[2] == "glue_a"


@pytest.mark.parametrize("result", ["error", "bad_id", "bad_object"])
def test_uncertain_spawn_is_saved_and_automatic_retry_is_refused(lua, result):
    game, engine, _ = supply_game(lua)
    lua.globals().spawn_result = result
    lua.execute("""
        alife_create_item=function(section,actor)
            engine.attempts=(engine.attempts or 0)+1
            if spawn_result=='error' then error('after possible side effect') end
            if spawn_result=='bad_id' then return {id=0} end
            return true
        end
    """)
    poll(game, engine)
    state = state_of(lua, game)
    assert state.deliveries[1].uncertain and not state.applying_reward
    assert "retry blocked" in game.tracker_view().delivery
    game.load_state(lua.table(gamma_archipelago_v1=state))
    poll(game, engine)
    assert engine.attempts == 1 and state_of(lua, game).received_count == 0


def test_creation_callbacks_cannot_generate_artefact_checks_and_method_ids_are_supported(lua):
    game, engine, _ = supply_game(lua, checks_artefacts=1)
    lua.globals().ap_delivery_game = game
    lua.globals().ap_delivery_artefact = artefact(lua, "af_medusa")
    lua.execute("""
        alife_create_item=function(section,actor)
            ap_delivery_game.actor_on_item_take(ap_delivery_artefact)
            return {id=function() return 200 end}
        end
    """)
    poll(game, engine)
    assert state_of(lua, game).received_count == 1
    assert not state_of(lua, game).checks[28052431]
    assert not list(state_of(lua, game).discoveries)


def test_disabled_unbound_unknown_receipts_and_conflicting_pending_history_are_refused(lua):
    game, _, _ = supply_game(lua)
    state = state_of(lua, game)
    module = lua.globals().gamma_ap_deliveries
    grant = lua.eval("function() return true end")
    assert module.receive(state, 28051812, grant)[0] is False
    state.deliveries = lua.table()
    state.allowed_items[28051001] = True
    assert module.receive(state, 28051001, grant)[0] is False
    state.session_key = None
    assert module.receive(state, 28051811, grant)[0] is False
    state.session_key = "a" * 64
    state.configuration.options.permission_supplies = 0
    assert module.receive(state, 28051811, grant)[0] is False


@pytest.mark.parametrize(
    "change",
    [
        "not_table",
        "bad_record",
        "wrong_id",
        "wrong_section",
        "bad_cursor",
        "bad_index",
        "bad_flag",
        "completed_uncertain",
        "unknown_key",
        "unbound",
        "disabled",
        "not_allowed",
    ],
)
def test_damaged_delivery_plans_refuse_load_without_acknowledgement(lua, change):
    game, _, _ = supply_game(lua)
    state = state_of(lua, game)
    record = state.deliveries[1]
    if change == "not_table":
        state.deliveries = 1
    elif change == "bad_record":
        state.deliveries[1] = False
    elif change == "wrong_id":
        record.item_id = 28051812
    elif change == "wrong_section":
        record.sections[1] = "unknown"
    elif change == "bad_cursor":
        record.next_action = 9
    elif change == "bad_index":
        record.sections[0] = "gun_oil"
    elif change == "bad_flag":
        record.uncertain = "yes"
    elif change == "completed_uncertain":
        record.next_action = 3
        record.uncertain = True
    elif change == "unknown_key":
        state.deliveries[4001] = record
    elif change == "unbound":
        state.session_key = None
    elif change == "disabled":
        state.configuration.options.permission_supplies = 0
    elif change == "not_allowed":
        state.allowed_items[record.item_id] = None
    game.load_state(lua.table(gamma_archipelago_v1=state))
    assert state_of(lua, game).refused_save


def test_legacy_save_and_completed_plan_validation(lua):
    game, engine, _ = supply_game(lua)
    poll(game, engine)
    module = lua.globals().gamma_ap_deliveries
    state = state_of(lua, game)
    assert module.validate(state)
    state.deliveries[1].item_id = 28051812
    assert not module.validate(state)
    state = state_of(lua, game)
    state.deliveries[1].next_action = 1
    assert not module.validate(state)
    state = state_of(lua, game)
    state.deliveries = None
    assert module.validate(state)
    game.load_state(lua.table(gamma_archipelago_v1=state))
    assert not list(state_of(lua, game).deliveries)


def test_preflight_and_permission_failure_cannot_repeat_completed_supply_actions(lua):
    game, engine, _ = supply_game(lua, ())
    state = state_of(lua, game)
    module = lua.globals().gamma_ap_deliveries
    grant = lua.eval("function() return false,'permission unavailable' end")
    engine.missing_section = "glue_a"
    assert module.receive(state, 28051811, grant)[0] is False
    assert not list(engine.created.values())
    engine.missing_section = None
    assert module.receive(state, 28051811, grant)[0] is False
    assert module.receive(state, 28051811, grant) == (False, "permission unavailable")
    assert list(engine.created.values()) == ["gun_oil", "glue_a"]
    assert module.validate(state)
    assert module.receive(state, 28051811, lua.eval("function() return true end")) is True
    assert list(engine.created.values()) == ["gun_oil", "glue_a"]
