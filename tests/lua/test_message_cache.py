"""Bounded presentation caches must fail closed without touching progression."""

import pytest

from gamma_archipelago.game_commands import decode_requests
from gamma_archipelago.notifications import Notice, encode_notices

from .test_communication import EPOCH, KEY, ROOT, setup, status, tick
from .test_game_adapter import saved_state
from .test_message_reload import LOG, feed, reload_messages


def state_for(lua):
    game, engine, _ = setup(lua)
    tick(game, engine)
    return saved_state(lua, game).gamma_archipelago_v1, engine


@pytest.mark.parametrize("name", [None, "", "x" * 65, "../owner", "a\\b", "a:b", "a\n"])
def test_native_owner_validation(lua, name):
    state, _ = state_for(lua)
    lua.globals().test_owner = name
    lua.execute("user_name=function() return test_owner end")
    reload_messages(lua)
    assert lua.globals().gamma_ap_game_run.load(state)[0] is None


@pytest.mark.parametrize("name", ["First Last", "Оуэн"])
def test_native_owner_allows_spaces_and_unicode(lua, name):
    state, engine = state_for(lua)
    lua.globals().test_owner = name
    lua.execute("user_name=function() return test_owner end")
    engine.files[f"D:/AnomalyAP/appdata/logs\\xray_{name}.log"] = engine.files[LOG]
    reload_messages(lua)
    assert len(lua.globals().gamma_ap_game_run.load(state).game) == 16


@pytest.mark.parametrize(
    "text",
    [
        None,
        "",
        "x" * 4096,
        "Game started: 00.11.2026 12:00:00.000",
        "Game started: 32.11.2026 12:00:00.000",
        "Game started: 27.00.2026 12:00:00.000",
        "Game started: 27.13.2026 12:00:00.000",
        "Game started: 27.11.2026 24:00:00.000",
        "Game started: 27.11.2026 12:60:00.000",
        "Game started: 27.11.2026 12:00:60.000",
    ],
)
def test_native_marker_missing_or_invalid(lua, text):
    state, engine = state_for(lua)
    engine.files[LOG] = text
    reload_messages(lua)
    assert lua.globals().gamma_ap_game_run.load(state)[0] is None


def test_native_marker_errors_and_forbidden_root(lua):
    state, engine = state_for(lua)
    reload_messages(lua)
    module = lua.globals().gamma_ap_game_run
    engine.fail_close = True
    assert module.load(state)[0] is None
    engine.fail_close = False
    engine.root = "D:/Anomaly/appdata/"
    assert module.load(state)[0] is None
    assert module.save(state, lua.table())[0] is False
    engine.root = "D:/AnomalyAP/appdata/"
    progress = module.load(state)
    engine.root = "D:/Anomaly/appdata/"
    assert module.load(state)[0] is None  # Even after the marker was cached.
    assert len(progress.game) == 16


def test_run_cache_roundtrip_and_foreign_identity_reset(lua):
    state, engine = state_for(lua)
    module = lua.globals().gamma_ap_game_run
    progress = module.load(state)
    progress.sequence, progress.ack, progress.entered = 8, 5, True
    assert module.save(state, progress) is True
    content = engine.files[ROOT + "game_run.txt"]
    restored = module.load(state)
    assert (restored.sequence, restored.ack, restored.entered) == (8, 5, True)
    for old, new in [
        (KEY, "d" * 64),
        ("configuration|-", "configuration|" + KEY),
        (progress.game, "0" * 16),
    ]:
        engine.files[ROOT + "game_run.txt"] = content.replace(old, new)
        reset = module.load(state)
        assert (reset.sequence, reset.ack, reset.entered) == (0, 0, False)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: s[:-1],
        lambda s: "x" * 2049,
        lambda s: s.replace("RUN|1", "RUN|2"),
        lambda s: s.replace(KEY, "a" * 63),
        lambda s: s.replace("configuration|-", "configuration|a-"),
        lambda s: s.replace("sequence|0", "sequence|00"),
        lambda s: s.replace("sequence|0", "sequence|1000000000"),
        lambda s: s.replace("ack|0", "ack|1"),
        lambda s: s.replace("entered|0", "entered|2"),
    ],
)
def test_invalid_run_cache_is_refused(lua, mutate):
    state, engine = state_for(lua)
    module = lua.globals().gamma_ap_game_run
    assert module.save(state, module.load(state)) is True
    engine.files[ROOT + "game_run.txt"] = mutate(engine.files[ROOT + "game_run.txt"])
    assert module.load(state)[0] is None


@pytest.mark.parametrize("failure", ["fail_open", "fail_write", "fail_close"])
def test_run_cache_io_failures(lua, failure):
    state, engine = state_for(lua)
    module = lua.globals().gamma_ap_game_run
    progress = module.load(state)
    setattr(engine, failure, True)
    assert module.save(state, progress)[0] is False
    if failure == "fail_close":
        assert module.load(state)[0] is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: s[:-1],
        lambda s: "x" * 1025,
        lambda s: s.replace("CURSOR|1", "CURSOR|2"),
        lambda s: s.replace("cursor|0", "cursor|00"),
        lambda s: s.replace("configuration|-", "configuration|a-"),
        lambda s: s.replace(KEY, "a" * 63),
    ],
)
def test_invalid_room_cursor_never_prints_history(lua, mutate):
    state, engine = state_for(lua)
    module = lua.globals().gamma_ap_room
    feed(engine, 1)
    assert module.poll(state, engine.now) is True
    engine.files[ROOT + "room_cursor.txt"] = mutate(engine.files[ROOT + "room_cursor.txt"])
    reload_messages(lua)
    feed(engine, 2, "Old event")
    assert lua.globals().gamma_ap_room.poll(state, engine.now)[0] is False
    assert not list(engine.news.values())


def test_room_cursor_read_failure(lua):
    state, engine = state_for(lua)
    feed(engine, 1)
    assert lua.globals().gamma_ap_room.poll(state, engine.now) is True
    reload_messages(lua)
    lua.execute("""
        local original=mock_io.open
        gamma_ap_room.io={open=function(path,mode)
            local file=original(path,mode)
            if file and path:find('room_cursor.txt',1,true) then
                file.close=function() return false end
            end
            return file
        end}
    """)
    assert lua.globals().gamma_ap_room.poll(state, engine.now)[0] is False


@pytest.mark.parametrize(
    "content",
    [
        "partial",
        "x" * 1048577,
        f"GAMMA_AP_NOTICES_ACK|1\nsession|{KEY}\nr:0\nr:0\nend|2\n",
        f"GAMMA_AP_NOTICES_ACK|1\nsession|{KEY}\n"
        + "".join(f"s:{index}:2:3\n" for index in range(8001))
        + "end|8001\n",
    ],
)
def test_invalid_notice_cache_cannot_announce_or_acknowledge(lua, content):
    state, engine = state_for(lua)
    engine.files[ROOT + "notices.txt"] = encode_notices(KEY, (Notice("s:1:2:3", 0, "New event"),))
    engine.files[ROOT + "notices_ack.txt"] = content
    assert lua.globals().gamma_ap_notifications.poll(state)[0] is False
    assert not list(engine.news.values())
    assert not list(state.notices_seen.values())


def test_foreign_notice_cache_does_not_suppress_current_session(lua):
    state, engine = state_for(lua)
    module = lua.globals().gamma_ap_notifications
    engine.files[ROOT + "notices.txt"] = encode_notices(KEY, (Notice("s:1:2:3", 0, "New event"),))
    engine.files[ROOT + "notices_ack.txt"] = module.encode_ack(
        "d" * 64, lua.table_from({"s:1:2:3": True})
    )
    assert module.poll(state) is True
    assert list(engine.news.values()) == ["New event"]


def test_notice_cache_read_close_failure(lua):
    state, engine = state_for(lua)
    engine.files[ROOT + "notices.txt"] = encode_notices(KEY, ())
    engine.files[ROOT + "notices_ack.txt"] = "partial"
    lua.execute("""
        local original=mock_io.open
        gamma_ap_notifications.io={open=function(path,mode)
            local file=original(path,mode)
            if file and path:find('notices_ack.txt',1,true) then
                file.close=function() return false end
            end
            return file
        end}
    """)
    assert lua.globals().gamma_ap_notifications.poll(state)[0] is False


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: s[:-1],
        lambda s: s.replace("COMMANDS|1", "COMMANDS|2"),
        lambda s: s.replace("target|" + EPOCH, "target|a"),
        lambda s: s.replace("end|1", "end|2"),
        lambda s: s.replace("request|1|", "request|01|"),
        lambda s: s.replace("request|1|", "request|1000000000|"),
        lambda s: s.replace("loaded|", "unknown|"),
        lambda s: s.replace("loaded|", "say|"),
        lambda s: s.replace("loaded|", "say|0a"),
        lambda s: s.replace("loaded|", "say|a"),
        lambda s: s.replace("loaded|", "say|" + "61" * 513),
    ],
)
def test_invalid_cached_requests_cannot_be_forwarded(lua, mutate):
    game, engine, _ = setup(lua)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    state = saved_state(lua, game).gamma_archipelago_v1
    engine.files[ROOT + "game_requests.txt"] = mutate(engine.files[ROOT + "game_requests.txt"])
    reload_messages(lua)
    module = lua.globals().gamma_ap_communication
    assert module.say(state, "Do not forward")[0] is False
    assert "cached AP request" in module.view(state, engine.now).status


def test_request_counter_and_cache_write_failure_keep_requests_recoverable(lua):
    game, engine, _ = setup(lua)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    state = saved_state(lua, game).gamma_archipelago_v1
    content = engine.files[ROOT + "game_run.txt"]
    engine.files[ROOT + "game_run.txt"] = content.replace("sequence|1", "sequence|999999999")
    reload_messages(lua)
    assert "exhausted" in lua.globals().gamma_ap_communication.say(state, "Overflow")[1]
    engine.files[ROOT + "game_run.txt"] = content
    # The request file may be newer than its separate presentation cache.
    engine.files[ROOT + "game_requests.txt"] = engine.files[ROOT + "game_requests.txt"].replace(
        "request|1|", "request|3|"
    )
    reload_messages(lua)
    tick(game, engine, heartbeat=3)
    tick(game, engine, heartbeat=4)
    assert "sequence|3" in engine.files[ROOT + "game_run.txt"]
    epoch, requests = decode_requests(engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH)
    assert [request.sequence for request in requests] == [3]
    assert lua.globals().gamma_ap_game_run.load(state).game == epoch
    # Fail only the cache boundary after the request file has been written.
    lua.execute("gamma_ap_game_run.save=function() return false,'Cache write failed' end")
    accepted, reason = lua.globals().gamma_ap_communication.say(state, "Recover me")
    assert accepted and reason == "Queued; Cache write failed"
    reload_messages(lua)
    tick(game, engine, heartbeat=5)
    tick(game, engine, heartbeat=6)
    assert "sequence|4" in engine.files[ROOT + "game_run.txt"]
    _, requests = decode_requests(engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH)
    assert [(request.sequence, request.text) for request in requests] == [
        (3, ""),
        (4, "Recover me"),
    ]


def test_cached_request_close_error_and_run_cache_error_surface(lua):
    state, engine = state_for(lua)
    engine.files[ROOT + "game_requests.txt"] = "partial"
    reload_messages(lua)
    lua.execute("""
        local original=mock_io.open
        gamma_ap_communication.io={open=function(path,mode)
            local file=original(path,mode)
            if file and path:find('game_requests.txt',1,true) then
                file.close=function() return false end
            end
            return file
        end}
    """)
    assert "close failed" in lua.globals().gamma_ap_communication.view(state, engine.now).status
    engine.files[ROOT + "game_run.txt"] = "partial"
    reload_messages(lua)
    module = lua.globals().gamma_ap_communication
    assert "Malformed game run cache" in module.view(state, engine.now).status
    assert module.flush(state, engine.now)[0] is False
    assert module.poll(state, engine.now)[0] is False


def test_exhausted_entry_counter_reports_failure_without_marking_entered(lua):
    game, engine, _ = setup(lua)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    state = saved_state(lua, game).gamma_archipelago_v1
    engine.files[ROOT + "game_run.txt"] = (
        engine.files[ROOT + "game_run.txt"]
        .replace("sequence|1", "sequence|999999999")
        .replace("entered|1", "entered|0")
    )
    engine.files[ROOT + "game_requests.txt"] = None
    reload_messages(lua)
    module = lua.globals().gamma_ap_communication
    engine.files[ROOT + "connection_status.txt"] = status(heartbeat=3)
    assert module.poll(state, engine.now) is True
    engine.files[ROOT + "connection_status.txt"] = status(heartbeat=4)
    assert "exhausted" in module.poll(state, engine.now + 1)[1]
    assert lua.globals().gamma_ap_game_run.load(state).entered is False
