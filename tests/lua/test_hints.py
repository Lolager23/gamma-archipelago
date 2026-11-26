from gamma_archipelago.room_feed import RoomMessage, encode_feed

from .test_communication import ROOT, setup, tick
from .test_game_adapter import saved_state
from .test_pda_ui import load_ui, panel_text
from .test_tracker import state_for, view


def test_hint_requests_use_official_ap_commands_without_completing_or_scouting_checks(lua):
    game, engine, _ = setup(lua)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    before = saved_state(lua, game).gamma_archipelago_v1
    assert game.request_hint("  Equipment Unlock: PDA  ")[0] is True
    assert game.request_hint("")[0] is True
    assert game.request_hint("x" * 481)[0] is False
    assert game.request_hint(None)[0] is False
    tick(game, engine, heartbeat=3)
    content = engine.files[ROOT + "game_requests.txt"]
    assert b"!hint Equipment Unlock: PDA".hex() in content
    assert b"!hint".hex() in content
    after = saved_state(lua, game).gamma_archipelago_v1
    assert dict(after.checks.items()) == dict(before.checks.items())
    assert not list(after.scout_requests.values())


def test_hint_projection_shows_bounded_server_replies_budget_and_cached_state(lua):
    game, engine, _ = setup(lua)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    module = lua.globals().gamma_ap_hints
    state = saved_state(lua, game).gamma_archipelago_v1
    empty = module.view(state, engine.now)
    assert "No server hint replies" in empty.lines[1]
    assert "Hint points: 4" in empty.budget and "Cost per item hint: 10" in empty.budget
    engine.files[ROOT + "room_feed.txt"] = encode_feed(
        state.session_key,
        None,
        "a" * 16,
        1,
        tuple(RoomMessage(i + 1, f"Server hint {i}") for i in range(64)),
    )
    result = module.view(state, engine.now)
    assert len(result.lines) == 32 and result.lines[1] == "Server hint 63"
    tick(game, engine, heartbeat=3, hint_cost=0)
    assert "Cost per item hint: 0" in module.view(state, engine.now).budget
    assert "Cached" in module.view(state, engine.now + 6000).budget
    engine.files[ROOT + "room_feed.txt"] = "partial"
    assert "room feed" in module.view(state, engine.now).lines[1]
    assert "No server hint replies" in module.view(lua.table(), engine.now).lines[1]
    assert game.tracker_view().hints is not None
    assert "Connected to AP server" in game.tracker_view().connection_status


def test_hint_tab_submits_item_and_refresh_requests_with_scrollable_replies(lua):
    module = load_ui(lua)
    current = view(lua, state_for(lua))
    current.hints = lua.table(
        budget="4 hint points; cost 10", lines=lua.table_from(["A hint", "Long reply " * 100])
    )
    requested = []
    lua.globals().gamma_ap_game = lua.table(
        tracker_view=lambda: current,
        request_hint=lambda item: (requested.append(item) or True, "Queued"),
    )
    window = module.get_ui()
    window.callbacks["hints"]()
    assert window.hints_page.IsShown(window.hints_page)
    assert not window.checks_page.IsShown(window.checks_page)
    assert not window.progress_page.IsShown(window.progress_page)
    assert "hint points" in panel_text(window.hint_budget)
    assert "A hint" in panel_text(window.hints)
    window.hint_input.SetText(window.hint_input, "Progressive Tools")
    window.callbacks["request_hint"]()
    window.callbacks["refresh_hints"]()
    assert requested == ["Progressive Tools", ""]
    assert "Queued" in panel_text(window.notice)
    current.bound = False
    window.refresh(window)
    assert not window.hints_page.IsShown(window.hints_page)
    assert not window.buttons.request_hint.IsEnabled(window.buttons.request_hint)


def test_disabled_scouting_hides_button_rewards_and_previews_but_keeps_hints(lua):
    module = load_ui(lua)
    current = view(lua, state_for(lua))
    current.scouting_enabled = False
    current.scouted = lua.table_from({current.rows[1].id: lua.table(item="Secret", player="Mini")})
    current.previews = lua.table_from(
        [lua.table(id=current.rows[1].id, label="Next side-task reward")]
    )
    lua.globals().gamma_ap_game = lua.table(tracker_view=lambda: current)
    window = module.get_ui()
    assert not window.buttons.scout.IsShown(window.buttons.scout)
    assert not window.buttons.scout.IsEnabled(window.buttons.scout)
    window.callbacks["scout"]()  # A stale/programmatic callback still cannot request scouting.
    assert "Secret" not in panel_text(window.selection)
    assert "not scouted" not in panel_text(window.selection)
    assert "Next side-task reward" not in panel_text(window.progress)
    assert window.buttons.hints.IsEnabled(window.buttons.hints)
    current.scouting_enabled = True
    window.refresh(window)
    assert window.buttons.scout.IsShown(window.buttons.scout)
    assert "Secret" in panel_text(window.selection)
