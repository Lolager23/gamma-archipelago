import pytest

from gamma_archipelago.game_commands import decode_requests, encode_status
from gamma_archipelago.protocol import encode_confirmed

from .test_game_adapter import enter_world, load_game, saved_state, set_incoming

KEY, EPOCH = "a" * 64, "b" * 16


def status(**changes):
    fields = dict(
        key=KEY,
        configuration=None,
        epoch=EPOCH,
        heartbeat=1,
        connected=True,
        address="localhost:4444",
        game_epoch=None,
        acknowledged=0,
        confirmed=3,
        hint_points=4,
        hint_cost=10,
        total=100,
    )
    return encode_status(**(fields | changes))


ROOT = "D:/AnomalyAP/appdata/archipelago\\"


def setup(lua):
    game, engine = load_game(lua)
    set_incoming(engine, items=())
    lua.execute("""
        engine.news={}
        db.actor.give_game_news=function(self,title,text)
            if engine.fail_news then error('UI') end
            engine.news[#engine.news+1]=text
        end
    """)
    engine.files[ROOT + "confirmed_checks.txt"] = encode_confirmed(KEY, frozenset())
    return game, engine, lua.globals().gamma_ap_communication


def tick(game, engine, **changes):
    engine.files[ROOT + "connection_status.txt"] = status(**changes)
    engine.now += 500
    game.actor_on_update()


def test_first_world_load_broadcast_request_is_not_repeated_by_save_load_or_level_switch(lua):
    game, engine, module = setup(lua)
    tick(game, engine, heartbeat=100)
    tick(game, engine, heartbeat=100)
    assert engine.files[ROOT + "game_requests.txt"] is None
    tick(game, engine, heartbeat=101)
    request = engine.files[ROOT + "game_requests.txt"]
    epoch, commands = decode_requests(request, KEY, None, EPOCH)
    assert commands[0].kind == "loaded"
    tick(game, engine, heartbeat=102, game_epoch=epoch, acknowledged=1)
    assert module.say(saved_state(lua, game).gamma_archipelago_v1, "Hello")[0] is True
    tick(game, engine, heartbeat=103, game_epoch=epoch, acknowledged=1)
    assert (
        decode_requests(engine.files[ROOT + "game_requests.txt"], KEY, None, EPOCH)[1][0].kind
        == "say"
    )
    tick(game, engine, heartbeat=104, game_epoch=epoch, acknowledged=2)
    game.load_state(saved_state(lua, game))
    engine.level = "l02_garbage"
    enter_world(engine)
    tick(game, engine, heartbeat=105, game_epoch=epoch, acknowledged=2)
    assert "loaded" not in engine.files[ROOT + "game_requests.txt"]
    assert not list(engine.news.values())  # The server's room chat is the announcement.


def test_status_uses_exact_confirmed_ids_and_stale_or_offline_status_is_explicit(lua):
    game, engine, module = setup(lua)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    state = saved_state(lua, game).gamma_archipelago_v1
    state.checks = lua.table()
    state.checks[28052003] = True
    assert module.view(state, engine.now).pending == 1
    engine.files[ROOT + "confirmed_checks.txt"] = encode_confirmed(KEY, frozenset({28052003}))
    assert module.view(state, engine.now).pending == 0
    assert game.print_connection_status() is True
    assert (
        "Checks awaiting server confirmation: 1" in engine.news[1]
    )  # Game owns its own copied state.
    assert "Cached" in module.view(state, engine.now + 6000).status
    assert "Cached" in module.view(state, 0).status
    tick(game, engine, heartbeat=3, connected=False)
    assert "Disconnected" in module.view(state, engine.now).status
    engine.files[ROOT + "connection_status.txt"] = status(heartbeat=1)
    assert "Outdated" in module.view(state, engine.now).status
    engine.files[ROOT + "confirmed_checks.txt"] = "partial"
    engine.files[ROOT + "connection_status.txt"] = status(heartbeat=4)
    assert module.view(state, engine.now).pending == "unknown"
    engine.files[ROOT + "connection_status.txt"] = "partial"
    assert "status" in module.view(state, engine.now).status
    engine.files[ROOT + "connection_status.txt"] = None
    assert "unavailable" in module.view(state, engine.now).status
    engine.files[ROOT + "connection_status.txt"] = status()
    engine.fail_close = True
    assert "close failed" in module.view(state, engine.now).status
    engine.fail_close = False
    engine.root = "D:/Anomaly/appdata/"
    assert "isolated" in module.view(state, engine.now).status
    assert game.print_connection_status() is True
    engine.alive = False
    assert game.print_connection_status() is False
    assert module.view(lua.table(), engine.now).pending == "unknown"


def test_queue_bounds_validation_and_write_failures(lua):
    game, engine, module = setup(lua)
    tick(game, engine)
    tick(game, engine, heartbeat=2)
    state = saved_state(lua, game).gamma_archipelago_v1
    assert module.say(lua.table(), "Hello")[0] is False
    for text in ("", "<unsafe>", "x" * 513):
        assert module.say(state, text)[0] is False
    assert game.send_ap_message("!hint")[0] is True
    for _ in range(30):
        assert module.say(state, "Message")[0] is True
    assert module.say(state, "Overflow")[0] is False
    engine.fail_open = True
    assert module.poll(state, engine.now)[0] is False
    engine.fail_open = False
    engine.fail_write = True
    assert module.poll(state, engine.now)[0] is False
    engine.fail_write = False
    engine.fail_news = True
    assert module.print_status(state) is False


def test_full_queue_flushes_before_entry_and_a_different_session_drops_old_chat(lua):
    game, engine, module = setup(lua)
    tick(game, engine)
    state = saved_state(lua, game).gamma_archipelago_v1
    for _ in range(32):
        assert module.say(state, "Pending")[0] is True
    tick(game, engine, heartbeat=2)
    content = engine.files[ROOT + "game_requests.txt"]
    assert "end|32" in content and "loaded" not in content
    other = lua.table(session_key="d" * 64)
    assert module.say(other, "New room")[0] is True
    # Rebind to the actual game: neither previous room's text may be forwarded.
    tick(game, engine, heartbeat=3)
    content = engine.files[ROOT + "game_requests.txt"]
    assert "loaded" in content and "end|1" in content
    assert b"Pending".hex() not in content and b"New room".hex() not in content


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: None,
        lambda s: "x" * 8193,
        lambda s: s[:-1],
        lambda s: s.replace("STATUS|1", "STATUS|2"),
        lambda s: s.replace(KEY, "c" * 64),
        lambda s: s.replace(EPOCH, "b" * 15),
        lambda s: s.replace("heartbeat|", "bad|"),
        lambda s: s.replace("confirmed|3", "confirmed|03"),
        lambda s: s.replace("ack|-|0", "ack|bad|0"),
        lambda s: s.replace("connection|1|", "connection|2|"),
        lambda s: s.replace("6c6f63616c686f73743a34343434", "a"),
        lambda s: s.replace("6c6f63616c686f73743a34343434", "25"),
    ],
)
def test_invalid_status_is_refused(lua, mutate):
    assert lua.globals().gamma_ap_communication.parse(mutate(status()), KEY, None)[0] is None
