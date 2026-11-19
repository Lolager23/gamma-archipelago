import pytest

from gamma_archipelago.notifications import Notice, encode_notices
from gamma_archipelago.presence import encode_presence

from .assertions import assert_lua_error
from .test_game_adapter import load_game, saved_state, set_incoming
from .test_loadout import configured_game

KEY, CONFIG, EPOCH = "a" * 64, "b" * 64, "c" * 16
PATH = "D:/AnomalyAP/appdata/archipelago\\presence.txt"


def packet(sequence=1, player="Оуэн", epoch=EPOCH, configuration=None):
    return encode_presence(KEY, configuration, epoch, sequence, player)


def setup(lua):
    game, engine = load_game(lua)
    lua.execute("""
        engine.news={}
        db.actor.give_game_news=function(self,title,text,icon,delay,duration)
            assert(title=="Archipelago" and duration==5000)
            if engine.fail_news then error("PDA unavailable") end
            engine.news[#engine.news+1]=text
        end
    """)
    set_incoming(engine, items=(28051003,))
    game.actor_on_update()
    return game, engine, lua.globals().gamma_ap_presence


def tick(game, engine, sequence, **fields):
    engine.files[PATH] = packet(sequence, **fields)
    engine.now += 500
    game.actor_on_update()


def test_join_requires_live_heartbeat_and_never_changes_receipts_checks_or_saved_state(lua):
    game, engine, _ = setup(lua)
    tick(game, engine, 1)
    assert not list(engine.news.values())
    tick(game, engine, 1)
    assert not list(engine.news.values())
    tick(game, engine, 2)
    assert list(engine.news.values()) == ["Оуэн joined the Archipelago."]
    before = saved_state(lua, game).gamma_archipelago_v1
    for count in (2, 3, 1, 4):
        tick(game, engine, count)
    after = saved_state(lua, game).gamma_archipelago_v1
    assert len(engine.news) == 1 and len(engine.created) == 1
    assert after.received_count == before.received_count == 1
    assert dict(after.checks.items()) == dict(before.checks.items())
    assert not any("presence" in name or "joined" in name for name in after)


def test_load_new_connection_and_reconnection_after_timeout_announce_once(lua):
    game, engine, _ = setup(lua)
    tick(game, engine, 1)
    tick(game, engine, 2)
    data = saved_state(lua, game)
    game.load_state(data)
    tick(game, engine, 2)
    assert len(engine.news) == 1
    tick(game, engine, 3)
    assert len(engine.news) == 2
    tick(game, engine, 1, epoch="d" * 16)
    tick(game, engine, 2, epoch="d" * 16)
    assert len(engine.news) == 3
    engine.now += 5001
    tick(game, engine, 2, epoch="d" * 16)
    assert len(engine.news) == 3
    tick(game, engine, 3, epoch="d" * 16)
    assert len(engine.news) == 4
    tick(game, engine, 4, epoch="d" * 16, player="Other alias")
    tick(game, engine, 5, epoch="d" * 16, player="Other alias")
    assert engine.news[5] == "Other alias joined the Archipelago."


@pytest.mark.parametrize(
    "template",
    [
        None,
        42,
        "missing-key",
        "%c[red]{player}",
        "{player}{player}",
        "{item}",
        "{player}{oops}",
        "A" * 513,
    ],
)
def test_missing_unsafe_or_malformed_translation_falls_back_to_english(lua, template):
    game, engine, _ = setup(lua)
    lua.globals().translation = template
    lua.execute("game={translate_string=function() return translation end}")
    tick(game, engine, 1, player="{player} Name")
    tick(game, engine, 2, player="{player} Name")
    assert engine.news[1] == "{player} Name joined the Archipelago."


def test_translation_retry_and_clock_reset(lua):
    game, engine, module = setup(lua)
    lua.execute('game={translate_string=function() return "Bienvenue {player}." end}')
    tick(game, engine, 1)
    engine.fail_news = True
    tick(game, engine, 2)
    assert not list(engine.news.values()) and len(engine.created) == 1
    engine.fail_news = False
    tick(game, engine, 3)
    assert engine.news[1] == "Bienvenue Оуэн."
    engine.now = 0
    engine.files[PATH] = packet(4)
    assert module.poll(saved_state(lua, game).gamma_archipelago_v1, 0) is True
    assert len(engine.news) == 2


@pytest.mark.parametrize("pda_mode", [1, 2])
def test_join_and_transfer_broadcasts_work_without_a_pda_and_do_not_replay(lua, pda_mode):
    game, engine, configuration = configured_game(
        lua, starting_pda=pda_mode, rewards_starting_gear_unlocks=int(pda_mode == 2)
    )
    lua.execute("""
        engine.news={}
        db.actor.give_game_news=function(self,title,text)
            engine.news[#engine.news+1]=text
        end
    """)
    game.on_game_start()
    engine.creation.new_game_faction = None
    notice_path = "D:/AnomalyAP/appdata/archipelago\\notices.txt"
    engine.files[notice_path] = encode_notices(
        KEY,
        (
            Notice("r:0", 1, "Friend gave you a Bandage"),
            Notice("s:1:2:42", 0, "You unlocked access for Friend"),
        ),
    )
    engine.files[PATH] = packet(1, configuration=configuration.digest)
    game.actor_on_update()
    state = saved_state(lua, game).gamma_archipelago_v1
    assert not lua.globals().gamma_ap_loadout.pda_available(state)
    tick(game, engine, 2, configuration=configuration.digest)
    assert list(engine.news.values()) == [
        "Friend gave you a Bandage",
        "You unlocked access for Friend",
        "Оуэн joined the Archipelago.",
    ]
    assert len(engine.created) == 1
    game.load_state(saved_state(lua, game))
    tick(game, engine, 3, configuration=configuration.digest)
    tick(game, engine, 4, configuration=configuration.digest)
    assert len(engine.news) == 4 and len(engine.created) == 1
    if pda_mode == 1:
        lua.globals().add_item(100, "pda", "D_PDA", "i_device", 0)
        tick(game, engine, 5, configuration=configuration.digest)
        assert len(engine.news) == 4 and len(engine.created) == 1


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: None,
        lambda s: "x" * 2049,
        lambda s: s[:-1],
        lambda s: "\n",
        lambda s: s.replace("PRESENCE|1", "PRESENCE|2"),
        lambda s: s.replace(KEY, "d" * 64),
        lambda s: s.replace("configuration|-", "configuration|" + CONFIG),
        lambda s: s.replace("end|1", "end|0"),
        lambda s: s.replace(EPOCH, "a" * 15),
        lambda s: s.replace(EPOCH, "bad!"),
        lambda s: s.replace("|1\nplayer", "|01\nplayer"),
        lambda s: s.replace("|1\nplayer", "|10000000000\nplayer"),
        lambda s: s.replace("player|" + "Оуэн".encode().hex(), "player|f"),
        lambda s: s.replace("player|" + "Оуэн".encode().hex(), "player|" + "61" * 385),
        lambda s: s.replace("player|" + "Оуэн".encode().hex(), "player|25"),
        lambda s: s.replace("player|" + "Оуэн".encode().hex(), "player|00"),
    ],
)
def test_malformed_cross_session_and_unsafe_data_never_announces(lua, mutate):
    assert_lua_error(lua.globals().gamma_ap_presence.parse(mutate(packet()), KEY, None))


def test_configured_packet_and_optional_file_failures_are_nonfatal_to_rewards(lua):
    game, engine, module = setup(lua)
    frame = module.parse(packet(configuration=CONFIG), KEY, CONFIG)
    assert frame.player == "Оуэн"
    assert module.poll(lua.table(), 0) is True
    engine.files[PATH] = packet()
    engine.fail_close = True
    state = saved_state(lua, game).gamma_archipelago_v1
    assert module.poll(state, 0)[0] is False
    engine.fail_close = False
    engine.files[PATH] = "broken\n"
    assert module.poll(state, 0)[0] is False
    engine.root = "D:/Anomaly/appdata/"
    assert module.poll(state, 0)[0] is False
