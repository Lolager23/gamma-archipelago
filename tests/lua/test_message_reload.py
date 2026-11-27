"""Engine-boundary regressions: reconstruct message modules, retaining disk only."""

import pytest

from gamma_archipelago.game_commands import decode_requests
from gamma_archipelago.notifications import Notice, encode_notices
from gamma_archipelago.room_feed import RoomMessage, encode_feed

from .conftest import ROOT as SOURCE
from .test_communication import EPOCH, KEY, ROOT, setup, tick
from .test_game_adapter import enter_world, saved_state

LOG = "D:/AnomalyAP/appdata/logs\\xray_test.log"


def reload_messages(lua):
    for name in ("game_run", "communication", "room", "notifications"):
        module = lua.globals().load_ap_module(
            str(SOURCE / "mod/gamedata/scripts" / f"gamma_ap_{name}.script")
        )
        module.io = lua.globals().mock_io
        lua.globals()[f"gamma_ap_{name}"] = module


def feed(engine, heartbeat, *texts, epoch=EPOCH):
    engine.files[ROOT + "room_feed.txt"] = encode_feed(
        KEY,
        None,
        epoch,
        heartbeat,
        tuple(RoomMessage(index, text) for index, text in enumerate(texts, 1)),
    )


def test_region_module_reload_does_not_replay_news_or_announce_another_join(lua):
    game, engine, _ = setup(lua)
    feed(engine, 1)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    epoch, _ = decode_requests(engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH)
    feed(engine, 2, "Mini found a reward")
    tick(game, engine, heartbeat=3, game_epoch=epoch, acknowledged=1)
    assert list(engine.news.values()) == ["Mini found a reward"]
    saved = saved_state(lua, game)
    reload_messages(lua)
    game.load_state(saved)
    engine.level = "l02_garbage"
    tick(game, engine, heartbeat=4, game_epoch=epoch, acknowledged=1)
    enter_world(engine)
    feed(engine, 3, "Mini found a reward")
    tick(game, engine, heartbeat=5, game_epoch=epoch, acknowledged=1)
    tick(game, engine, heartbeat=6, game_epoch=epoch, acknowledged=1)
    feed(engine, 4, "Mini found a reward")
    tick(game, engine, heartbeat=7, game_epoch=epoch, acknowledged=1)
    assert list(engine.news.values()) == ["Mini found a reward"]
    current_epoch, requests = decode_requests(
        engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH
    )
    assert current_epoch == epoch
    assert all(request.sequence <= 1 for request in requests)


def test_new_room_events_during_loading_wait_then_display_once_after_reload(lua):
    game, engine, _ = setup(lua)
    feed(engine, 1)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    saved = saved_state(lua, game)
    reload_messages(lua)
    game.load_state(saved)
    feed(engine, 2, "Reward during loading")
    tick(game, engine, heartbeat=3)
    feed(engine, 3, "Reward during loading")
    tick(game, engine, heartbeat=4)
    assert not list(engine.news.values())
    enter_world(engine)
    tick(game, engine, heartbeat=5)
    tick(game, engine, heartbeat=6)
    assert list(engine.news.values()) == ["Reward during loading"]


def test_first_upgrade_skips_cached_history_but_preserves_later_events(lua):
    game, engine, _ = setup(lua)
    feed(engine, 1, "Historical buffer")
    tick(game, engine)
    feed(engine, 2, "Historical buffer", "New event")
    tick(game, engine, heartbeat=2)
    tick(game, engine, heartbeat=3)
    assert list(engine.news.values()) == ["New event"]
    # A fresh companion owns a fresh sequence namespace.
    feed(engine, 1, "New companion event", epoch="c" * 16)
    tick(game, engine, heartbeat=4)
    feed(engine, 2, "New companion event", epoch="c" * 16)
    tick(game, engine, heartbeat=5)
    assert list(engine.news.values())[-1] == "New companion event"


def test_pending_chat_survives_module_reload_without_requeuing_entry(lua):
    game, engine, module = setup(lua)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    epoch, _ = decode_requests(engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH)
    tick(game, engine, heartbeat=3, game_epoch=epoch, acknowledged=1)
    state = saved_state(lua, game).gamma_archipelago_v1
    assert module.say(state, "Pending chat")[0] is True
    reload_messages(lua)
    tick(game, engine, heartbeat=4, game_epoch=epoch, acknowledged=1)
    tick(game, engine, heartbeat=5, game_epoch=epoch, acknowledged=1)
    restored_epoch, requests = decode_requests(
        engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH
    )
    assert restored_epoch == epoch
    assert [(request.sequence, request.kind, request.text) for request in requests] == [
        (2, "say", "Pending chat")
    ]
    tick(game, engine, heartbeat=6, game_epoch=epoch, acknowledged=2)
    reload_messages(lua)
    tick(game, engine, heartbeat=7, game_epoch=epoch, acknowledged=2)
    tick(game, engine, heartbeat=8, game_epoch=epoch, acknowledged=2)
    assert "loaded" not in engine.files[ROOT + "game_requests.txt"]
    module = lua.globals().gamma_ap_communication
    assert module.say(saved_state(lua, game).gamma_archipelago_v1, "Next")[0] is True
    _, requests = decode_requests(engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH)
    assert [(request.sequence, request.text) for request in requests] == [(3, "Next")]


def test_real_native_process_start_gets_a_new_single_entry_request(lua):
    game, engine, _ = setup(lua)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    old_epoch, _ = decode_requests(engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH)
    tick(game, engine, heartbeat=3, game_epoch=old_epoch, acknowledged=1)
    engine.files[LOG] = "Game started: 27.11.2026 05:00:00.001\n"
    reload_messages(lua)
    tick(game, engine, heartbeat=4, game_epoch=old_epoch, acknowledged=1)
    tick(game, engine, heartbeat=5, game_epoch=old_epoch, acknowledged=1)
    new_epoch, requests = decode_requests(
        engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH
    )
    assert new_epoch != old_epoch
    assert [(request.sequence, request.kind) for request in requests] == [(1, "loaded")]


def test_old_save_uses_durable_notice_ack_without_replaying_or_reapplying(lua):
    game, engine, _ = setup(lua)
    tick(game, engine)
    old_save = saved_state(lua, game)
    engine.files[ROOT + "notices_ack.txt"] = lua.globals().gamma_ap_notifications.encode_ack(
        KEY, lua.table_from({"s:1:2:3": True})
    )
    engine.files[ROOT + "notices.txt"] = encode_notices(
        KEY, (Notice("s:1:2:3", 0, "Old reward"), Notice("s:3:2:4", 0, "New reward"))
    )
    reload_messages(lua)
    game.load_state(old_save)
    enter_world(engine)
    tick(game, engine, heartbeat=2)
    tick(game, engine, heartbeat=3)
    assert list(engine.news.values()) == ["New reward"]
    assert not list(engine.created.values())


@pytest.mark.parametrize("failure", ["open", "write", "close"])
def test_cursor_write_retry_does_not_repeat_displayed_news(lua, failure):
    game, engine, _ = setup(lua)
    feed(engine, 1)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    state = saved_state(lua, game).gamma_archipelago_v1
    feed(engine, 2, "One event")
    lua.execute(f"""
        local original=mock_io.open
        gamma_ap_room.io={{open=function(path,mode)
            if path:find('room_cursor.txt',1,true) and mode=='wb' then
                if '{failure}'=='open' then return nil end
                local file=original(path,mode)
                if '{failure}'=='write' then file.write=function() return nil end end
                if '{failure}'=='close' then file.close=function() return false end end
                return file
            end
            return original(path,mode)
        end}}
    """)
    module = lua.globals().gamma_ap_room
    assert module.poll(state, engine.now)[0] is False
    assert module.poll(state, engine.now + 1)[0] is False
    assert list(engine.news.values()) == ["One event"]
    module.io = lua.globals().mock_io
    assert module.poll(state, engine.now + 2) is True
    assert list(engine.news.values()) == ["One event"]
