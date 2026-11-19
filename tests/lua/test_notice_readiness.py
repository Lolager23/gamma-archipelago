import pytest

from gamma_archipelago.notifications import Notice, encode_notices
from gamma_archipelago.presence import encode_presence

from .test_game_adapter import enter_world, load_game, saved_state, set_incoming

KEY = "a" * 64
BRIDGE = "D:/AnomalyAP/appdata/archipelago\\"


def loading_game(lua):
    game, engine = load_game(lua)
    lua.execute("""
        engine.news={}; engine.frame=100; engine.precache=20; engine.paused=false
        device=function() return {
            frame=engine.frame,precache_frame=engine.precache,
            is_paused=function() return engine.paused end}
        end
        level.present=function() return engine.present ~= false end
        db.actor.give_game_news=function(self,title,text)
            if engine.fail_news then error('display failed') end
            engine.news[#engine.news+1]=text
        end
    """)
    game.on_game_start()
    set_incoming(engine, items=(28051003,))
    engine.files[BRIDGE + "notices.txt"] = encode_notices(
        KEY,
        (
            Notice("r:0", 1, "Friend gave you a Bandage"),
            Notice("s:1:2:42", 0, "You unlocked access for Friend"),
        ),
    )
    return game, engine


def tick(game, engine, sequence):
    engine.now += 500
    engine.frame += 1
    engine.files[BRIDGE + "presence.txt"] = encode_presence(KEY, None, "c" * 16, sequence, "Player")
    game.actor_on_update()


@pytest.mark.parametrize("precache", [20, 0], ids=["loading", "enter-zone-prompt"])
def test_alive_actor_cannot_display_or_acknowledge_notices_before_dismissal(lua, precache):
    game, engine = loading_game(lua)
    engine.precache = precache
    for sequence in range(1, 5):
        tick(game, engine, sequence)
    assert not list(engine.news.values())
    state = saved_state(lua, game).gamma_archipelago_v1
    assert not list(state.notices_seen.keys())
    assert engine.files[BRIDGE + "notices_ack.txt"] is None
    assert state.received_count == 1 and len(engine.created) == 1


def test_prompt_and_same_frame_dismissal_wait_then_flush_each_notice_once(lua):
    game, engine = loading_game(lua)
    tick(game, engine, 1)
    engine.precache = 0
    engine.callbacks.on_loading_screen_key_prompt()
    tick(game, engine, 2)
    assert not list(engine.news.values())
    engine.callbacks.on_loading_screen_dismissed()
    state = saved_state(lua, game).gamma_archipelago_v1
    assert lua.globals().gamma_ap_notifications.poll(state) is True
    assert lua.globals().gamma_ap_presence.poll(state, engine.now) is True
    assert engine.files[BRIDGE + "notices_ack.txt"] is None
    assert not list(engine.news.values())
    for sequence in range(3, 7):
        tick(game, engine, sequence)
    assert list(engine.news.values()) == [
        "Friend gave you a Bandage",
        "You unlocked access for Friend",
        "Player joined the Archipelago.",
    ]
    assert len(engine.created) == 1


@pytest.mark.parametrize("boundary", ["load", "prompt", "destroy", "new-game"])
def test_readiness_closes_again_on_each_loading_boundary(lua, boundary):
    game, engine = loading_game(lua)
    engine.precache = 0
    enter_world(engine)
    ready = lua.globals().gamma_ap_readiness
    assert ready.ready() is True
    if boundary == "load":
        game.load_state(saved_state(lua, game))
    elif boundary == "prompt":
        engine.callbacks.on_loading_screen_key_prompt()
    elif boundary == "destroy":
        engine.callbacks.actor_on_net_destroy()
    else:
        game.on_game_start()
    for sequence in (1, 2):
        tick(game, engine, sequence)
    assert not list(engine.news.values()) and ready.ready() is False
    enter_world(engine)
    for sequence in (3, 4, 5):
        tick(game, engine, sequence)
    assert len(engine.news) == 3


@pytest.mark.parametrize(
    "blocked",
    [
        "engine.precache=1",
        "engine.paused=true",
        "engine.present=false",
        "db.actor=nil",
        "engine.alive=false",
        "device=nil",
        "level.present=nil",
        "engine.frame=99",
    ],
)
def test_dismissal_still_requires_an_alive_unpaused_world_after_precache(lua, blocked):
    _, engine = loading_game(lua)
    engine.precache = 0
    enter_world(engine)
    readiness = lua.globals().gamma_ap_readiness
    assert readiness.ready() is True
    lua.execute(blocked)
    assert readiness.ready() is False


@pytest.mark.parametrize("device_value", ["nil", "{}", "{frame='bad'}"])
def test_failed_or_missing_native_frame_cannot_release_the_gate(lua, device_value):
    _, engine = loading_game(lua)
    lua.execute("device=function() return " + device_value + " end")
    engine.callbacks.on_loading_screen_dismissed()
    assert lua.globals().gamma_ap_readiness.ready() is False


def test_reload_keeps_unshown_notices_pending_and_preserves_displayed_identities(lua):
    game, engine = loading_game(lua)
    engine.precache = 0
    enter_world(engine)
    for sequence in range(1, 4):
        tick(game, engine, sequence)
    assert len(engine.news) == 3
    stored = saved_state(lua, game)
    engine.files[BRIDGE + "notices.txt"] = encode_notices(
        KEY,
        (
            Notice("r:0", 1, "Friend gave you a Bandage"),
            Notice("s:2:2:42", 0, "A new outgoing reward"),
        ),
    )
    game.load_state(stored)
    for sequence in (4, 5):
        tick(game, engine, sequence)
    assert len(engine.news) == 3
    assert saved_state(lua, game).gamma_archipelago_v1.notices_seen["s:2:2:42"] is None
    enter_world(engine)
    for sequence in (6, 7, 8):
        tick(game, engine, sequence)
    assert list(engine.news.values())[3:] == [
        "A new outgoing reward",
        "Player joined the Archipelago.",
    ]
    assert len(engine.created) == 1
