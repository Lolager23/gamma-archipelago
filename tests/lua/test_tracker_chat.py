import pytest

from gamma_archipelago.game_commands import decode_requests

from .test_communication import EPOCH, KEY, ROOT, setup, tick
from .test_pda_ui import load_ui, panel_text
from .test_tracker import state_for, view


def chat_window(lua, *, accepted=True):
    module = load_ui(lua)
    current = view(lua, state_for(lua))
    submitted = []

    def send(text):
        submitted.append(text)
        return accepted, "Queued" if accepted else "AP message queue is full"

    lua.globals().gamma_ap_game = lua.table(
        tracker_view=lambda: current, send_ap_message=send, flush_ap_messages=lambda: True
    )
    window = module.get_ui()
    window.callbacks["hints"]()
    return window, current, submitted


@pytest.mark.parametrize(
    "text",
    [
        "Hello everyone",
        "!hint",
        "!hint Progressive Tools",
        "Hello !hint",
        "  100% [ready] <ok> | go  ",
    ],
)
@pytest.mark.parametrize("action", ["send_chat", "chat_input"])
def test_send_and_enter_submit_exact_text_once_and_clear_only_on_acceptance(lua, text, action):
    window, _, submitted = chat_window(lua)
    window.chat_input.SetText(window.chat_input, text)
    window.callbacks[action]()
    assert submitted == [text]
    assert window.chat_input.GetText(window.chat_input) == ""
    assert "Queued" in panel_text(window.notice)
    window.callbacks[action]()
    assert submitted == [text]
    assert "Enter a message" in panel_text(window.notice)


def test_rejected_submission_preserves_the_draft_and_reports_the_queue_problem(lua):
    window, _, submitted = chat_window(lua, accepted=False)
    window.chat_input.SetText(window.chat_input, "!hint PDA")
    window.callbacks["send_chat"]()
    assert submitted == ["!hint PDA"]
    assert window.chat_input.GetText(window.chat_input) == "!hint PDA"
    assert "queue is full" in panel_text(window.notice)


def test_blank_hidden_and_disabled_inputs_cannot_accidentally_send_chat(lua):
    window, current, submitted = chat_window(lua)
    window.chat_input.SetText(window.chat_input, "   ")
    window.callbacks["send_chat"]()
    assert not submitted
    window.chat_input.SetText(window.chat_input, "Draft")
    window.callbacks["checks"]()
    window.callbacks["chat_input"]()  # A hidden edit box must not send on a stale event.
    assert not submitted
    window.callbacks["hints"]()
    assert window.chat_input.GetText(window.chat_input) == "Draft"
    current.bound = False
    window.refresh(window)
    assert not window.chat_input.IsEnabled(window.chat_input)
    assert not window.buttons.send_chat.IsEnabled(window.buttons.send_chat)
    window.callbacks["send_chat"]()
    assert not submitted


def test_game_bridge_preserves_chat_and_command_payloads_without_adding_or_stripping_prefixes(lua):
    game, engine, _ = setup(lua)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    for text in (
        "Hello everyone",
        "!hint",
        "!hint Progressive Tools",
        "  100% [ready] <ok> | go  ",
    ):
        assert game.send_ap_message(text)[0] is True
    tick(game, engine, heartbeat=3)
    _, requests = decode_requests(engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH)
    assert [entry.text for entry in requests if entry.kind == "say"] == [
        "Hello everyone",
        "!hint",
        "!hint Progressive Tools",
        "  100% [ready] <ok> | go  ",
    ]


def test_manual_chat_flushes_while_paused_without_announcing_automatic_world_entry(lua):
    game, engine, module = setup(lua)
    tick(game, engine)
    engine.paused = True
    assert game.send_ap_message("Hello while paused")[0] is True
    assert engine.files[ROOT + "game_requests.txt"] is None  # No fresh companion yet.
    from .test_communication import status

    engine.files[ROOT + "connection_status.txt"] = status(heartbeat=2)
    assert game.flush_ap_messages() is True
    _, requests = decode_requests(engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH)
    assert [(entry.kind, entry.text) for entry in requests] == [("say", "Hello while paused")]
    assert module.flush(lua.table(), engine.now) is True


def test_failed_immediate_write_keeps_the_accepted_message_for_retry(lua):
    game, engine, _ = setup(lua)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    engine.paused = True
    engine.fail_open = True
    accepted, reason = game.send_ap_message("Retry this chat")
    assert accepted and reason.startswith("Queued;")
    engine.fail_open = False
    assert game.flush_ap_messages() is True
    _, requests = decode_requests(engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH)
    assert sum(entry.text == "Retry this chat" for entry in requests) == 1


def test_visible_chat_refresh_flushes_pending_requests_once_per_second_and_reports_failure(lua):
    window, _, _ = chat_window(lua)
    lua.execute("time_global=function() return 1000 end")
    flushed = []
    lua.globals().gamma_ap_game.flush_ap_messages = lambda: (
        flushed.append(True) or False,
        "AP game request write failed",
    )
    window.Update(window)
    window.Update(window)
    assert len(flushed) == 1
    assert "write failed" in panel_text(window.notice)
    lua.globals().clock += 1000
    lua.globals().gamma_ap_game.flush_ap_messages = lambda: flushed.append(True) or True
    window.Update(window)
    assert len(flushed) == 2
    window.callbacks["checks"]()
    lua.globals().clock += 1000
    window.Update(window)
    assert len(flushed) == 2


def test_paused_game_clock_does_not_keep_stopped_companion_status_online(lua):
    game, engine, _ = setup(lua)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    engine.paused = True
    engine.continual_now = engine.now + 6000
    assert "Cached" in game.tracker_view().connection_status
    from .test_communication import status

    engine.files[ROOT + "connection_status.txt"] = status(heartbeat=3)
    assert "Connected" in game.tracker_view().connection_status
    engine.continual_now += 6000
    assert game.print_connection_status() is True
    assert "Cached" in engine.news[len(engine.news)]
