import pytest

from gamma_archipelago.notifications import Notice, decode_acknowledgements, encode_notices

from .assertions import assert_lua_error
from .test_game_adapter import enter_world, load_game, saved_state, set_incoming

KEY = "a" * 64


@pytest.mark.parametrize("item", [0, 10**10, 2**53 - 1, -(2**53 - 1)])
def test_foreign_item_identity_roundtrips_without_numeric_rounding(lua, item):
    module = lua.globals().gamma_ap_notifications
    identity = f"s:28052001:2:{item}"
    encoded = encode_notices(KEY, (Notice(identity, 0, "Foreign reward"),))
    assert module.parse(encoded, KEY)[1].id == identity
    acknowledged = module.encode_ack(KEY, lua.table_from({identity: True}))
    assert decode_acknowledgements(acknowledged, KEY) == {identity}


@pytest.mark.parametrize("item", [str(2**53), str(-(2**53)), "-0", "-01", "9" * 17])
def test_lua_refuses_noncanonical_or_out_of_range_foreign_item_ids(lua, item):
    identity = f"s:28052001:2:{item}"
    assert (
        lua.globals().gamma_ap_notifications.encode_ack(KEY, lua.table_from({identity: True}))[0]
        is None
    )


def packet(*notices, key=KEY):
    return encode_notices(key, notices)


def test_notification_waits_for_actual_delivery_and_does_not_repeat_after_reload(lua):
    game, engine = load_game(lua)
    lua.execute("""
        engine.news={}
        db.actor.give_game_news=function(self,title,text,icon,delay,duration)
            assert(title=='Archipelago' and duration==5000)
            if engine.fail_news then error('PDA unavailable') end
            engine.news[#engine.news+1]=text
        end
    """)
    set_incoming(engine, items=(28051003, 28051001))
    engine.files["D:/AnomalyAP/appdata/archipelago\\notices.txt"] = packet(
        Notice("r:1", 2, "Оуэн gave you a Basic Toolkit"),
        Notice("s:3:2:4", 0, "You gave Friend Rupees"),
    )
    game.actor_on_update()
    assert list(engine.news.values()) == ["You gave Friend Rupees"]
    engine.now += 500
    engine.fail_news = True
    game.actor_on_update()
    assert list(engine.created.values()) == ["bandage", "itm_basickit"]
    engine.fail_news = False
    engine.now += 500
    game.actor_on_update()
    assert list(engine.news.values())[-1] == "Оуэн gave you a Basic Toolkit"
    acknowledged = engine.files["D:/AnomalyAP/appdata/archipelago\\notices_ack.txt"]
    assert decode_acknowledgements(acknowledged, KEY) == {"r:1", "s:3:2:4"}
    game.load_state(saved_state(lua, game))
    enter_world(engine)
    engine.now += 500
    game.actor_on_update()
    assert len(engine.news) == 2 and len(engine.created) == 2


@pytest.mark.parametrize(
    "content",
    [
        None,
        "x" * 131073,
        "incomplete",
        "\n",
        "GAMMA_AP_NOTICES|1\n",
        packet(key="b" * 64),
        packet().replace("end|0", "end|01"),
        packet().replace("end|0", "end|1"),
        f"GAMMA_AP_NOTICES|1\nsession|{KEY}\nend|17\n",
        f"GAMMA_AP_NOTICES|1\nsession|{KEY}\nnotice|r:0|1|f\nend|1\n",
        f"GAMMA_AP_NOTICES|1\nsession|{KEY}\nnotice|r:0|0|61\nend|1\n",
        f"GAMMA_AP_NOTICES|1\nsession|{KEY}\nnotice|s:1:2:3|1|61\nend|1\n",
        f"GAMMA_AP_NOTICES|1\nsession|{KEY}\nnotice|bad|0|61\nend|1\n",
        f"GAMMA_AP_NOTICES|1\nsession|{KEY}\nnotice|r:4000|1|61\nend|1\n",
        f"GAMMA_AP_NOTICES|1\nsession|{KEY}\nnotice|r:00|1|61\nend|1\n",
        f"GAMMA_AP_NOTICES|1\nsession|{KEY}\nnotice|r:0|1|25\nend|1\n",
    ],
)
def test_malformed_or_wrong_session_sidecars_are_refused_before_display(lua, content):
    result = lua.globals().gamma_ap_notifications.parse(content, KEY)
    assert_lua_error(result)


def test_duplicate_identity_and_invalid_receipt_fields_are_refused(lua):
    line = "notice|r:0|1|61"
    duplicates = f"GAMMA_AP_NOTICES|1\nsession|{KEY}\n{line}\n{line}\nend|2\n"
    module = lua.globals().gamma_ap_notifications
    assert_lua_error(module.parse(duplicates, KEY))
    for bad in ["4001", "01", "bad"]:
        assert_lua_error(module.parse(duplicates.replace("|1|61", f"|{bad}|61"), KEY))
    for identity in ["r:4000", "s:01:2:3", "s:1:01:3", "s:1:2:01", "bad"]:
        assert_lua_error(module.encode_ack(KEY, lua.table_from({identity: True})))
    assert_lua_error(module.encode_ack(KEY, lua.table_from({"r:0": False})))
    assert_lua_error(module.encode_ack(KEY, lua.table_from({1: True})))
    many = {f"s:{index}:2:3": True for index in range(8001)}
    assert_lua_error(module.encode_ack(KEY, lua.table_from(many)))


def test_notification_file_failures_never_reapply_a_reward(lua):
    game, engine = load_game(lua)
    module = lua.globals().gamma_ap_notifications
    state = lua.globals().gamma_ap_state.new_state()
    state.session_key = KEY
    engine.root = "D:/Anomaly/appdata/"
    assert module.poll(state)[0] is False
    engine.root = "D:/AnomalyAP/appdata/"
    engine.files["D:/AnomalyAP/appdata/archipelago\\notices.txt"] = packet()
    engine.fail_close = True
    assert module.poll(state)[0] is False
    engine.fail_close = False
    engine.files["D:/AnomalyAP/appdata/archipelago\\notices.txt"] = "bad"
    assert module.poll(state)[0] is False
    engine.files["D:/AnomalyAP/appdata/archipelago\\notices.txt"] = packet()
    state.notices_seen["bad"] = True
    assert module.poll(state)[0] is False
    state.notices_seen["bad"] = None
    engine.fail_open = True
    assert module.poll(state)[0] is False
    engine.fail_open = False
    engine.fail_write = True
    assert module.poll(state)[0] is False
