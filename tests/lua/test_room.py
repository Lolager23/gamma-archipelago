import pytest

from gamma_archipelago.room_feed import RoomMessage, encode_feed

from .test_game_adapter import enter_world, load_game, saved_state, set_incoming

KEY = "a" * 64
PATH = "D:/AnomalyAP/appdata/archipelago\\room_feed.txt"


def packet(heartbeat=10, text="Dave gave Sword to Dave."):
    return encode_feed(
        KEY, None, "b" * 16, heartbeat, (RoomMessage(1, text), RoomMessage(2, "Hello"))
    )


def test_live_feed_waits_for_readiness_and_advance_without_replay_on_level_load(lua):
    game, engine = load_game(lua)
    lua.execute("""
        engine.news={}
        db.actor.give_game_news=function(self,title,text)
            if engine.fail_news then error('UI') end
            engine.news[#engine.news+1]=text
        end
    """)
    set_incoming(engine, items=())
    module = lua.globals().gamma_ap_room
    engine.files[PATH] = packet()
    game.actor_on_update()
    engine.now += 500
    game.actor_on_update()
    assert not list(engine.news.values())  # Static cached feed cannot announce.
    engine.files[PATH] = packet(11)
    engine.fail_news = True
    engine.now += 500
    game.actor_on_update()
    assert not list(engine.news.values())
    engine.fail_news = False
    engine.now += 500
    game.actor_on_update()
    assert engine.news[1] == "Dave gave Sword to Dave."
    data = saved_state(lua, game)
    game.load_state(data)
    engine.now += 500
    game.actor_on_update()
    assert len(engine.news) == 1  # Loading gate closed.
    enter_world(engine)
    engine.now += 500
    game.actor_on_update()
    assert len(engine.news) == 2
    engine.now += 6000
    assert module.poll(data.gamma_archipelago_v1, engine.now) is True
    engine.now = 1
    assert module.poll(data.gamma_archipelago_v1, 1) is True
    assert len(engine.news) == 2 and not data.gamma_archipelago_v1.notices_seen["1"]
    engine.fail_close = True
    assert module.poll(data.gamma_archipelago_v1, 2)[0] is False
    engine.fail_close = False
    engine.files[PATH] = "partial"
    assert module.poll(data.gamma_archipelago_v1, 3)[0] is False
    engine.root = "D:/Anomaly/appdata/"
    assert module.poll(data.gamma_archipelago_v1, 4)[0] is False
    assert module.poll(lua.table(), 4) is True


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: None,
        lambda s: "x" * 280001,
        lambda s: s[:-1],
        lambda s: s.replace("ROOM|1", "ROOM|2"),
        lambda s: s.replace(KEY, "c" * 64),
        lambda s: s.replace("configuration|-", "configuration|" + KEY),
        lambda s: s.replace("b" * 16, "b" * 15),
        lambda s: s.replace("|10\n", "|0\n"),
        lambda s: s.replace("end|2", "end|1"),
        lambda s: s.replace("message|2|", "message|1|"),
        lambda s: s.replace("message|1|", "message|01|"),
        lambda s: s.replace("message|2|48656c6c6f", "message|2|a"),
        lambda s: s.replace("48656c6c6f", "3c"),
        lambda s: s.replace("48656c6c6f", "a" * 4098),
    ],
)
def test_malformed_room_feed_never_reaches_the_native_ui(lua, mutate):
    assert lua.globals().gamma_ap_room.parse(mutate(packet()), KEY, None)[0] is None


def test_empty_and_unicode_feed_parsing(lua):
    module = lua.globals().gamma_ap_room
    assert module.parse(encode_feed(KEY, KEY, "a" * 16, 1, ()), KEY, KEY).heartbeat == 1
    assert module.parse(packet(text="Оуэн"), KEY, None).messages[1].text == "Оуэн"
