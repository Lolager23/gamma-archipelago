import pytest

from gamma_archipelago.catalog import GAME
from gamma_archipelago.notifications import Notice, encode_notices, transfer_notice

from .assertions import assert_lua_error
from .test_game_adapter import load_game, saved_state, set_incoming

KEY = "a" * 64


def semantic(*, outgoing=False, item_id=28051001, game=GAME):
    return transfer_notice(
        "s:3:2:4" if outgoing else "r:0",
        0 if outgoing else 1,
        "{item}",
        "Basic Toolkit",
        item_id=item_id,
        game=game,
        outgoing=outgoing,
    )


def parsed(lua, notice):
    return lua.globals().gamma_ap_notifications.parse(encode_notices(KEY, (notice,)), KEY)[1]


def translator(lua, entries):
    lua.globals().translations = lua.table_from(entries)
    lua.execute("game={translate_string=function(key) return translations[key] or key end}")


def test_missing_translation_and_engine_api_fall_back_to_english(lua):
    notice = semantic()
    assert lua.globals().gamma_ap_notice_text.render(parsed(lua, notice)) == notice.text
    translator(lua, {})
    assert lua.globals().gamma_ap_notice_text.render(parsed(lua, notice)) == notice.text
    legacy = Notice("r:0", 1, "Saved old text")
    assert lua.globals().gamma_ap_notice_text.render(parsed(lua, legacy)) == legacy.text


@pytest.mark.parametrize("outgoing", [False, True])
@pytest.mark.parametrize("item_id", [28051001, 28051401])
def test_all_transfer_kinds_roundtrip_through_the_native_parser(lua, outgoing, item_id):
    notice = semantic(outgoing=outgoing, item_id=item_id)
    translator(lua, {})
    assert lua.globals().gamma_ap_notice_text.render(parsed(lua, notice)) == notice.text


def test_game_selected_translation_reorders_fields_without_recursive_substitution(lua):
    translator(
        lua,
        {
            "gamma_ap_notice_received_item": '"{item}" from {player}.',
            "gamma_ap_reward_28051001": "Translated toolkit",
        },
    )
    result = lua.globals().gamma_ap_notice_text.render(parsed(lua, semantic()))
    assert result == '"Translated toolkit" from {item}.'
    foreign = semantic(game="Foreign Game")
    assert (
        lua.globals().gamma_ap_notice_text.render(parsed(lua, foreign))
        == '"Basic Toolkit" from {item}.'
    )


@pytest.mark.parametrize(
    "template",
    [
        "",
        "%c[red]{player}{item}",
        "{player}",
        "{item}{item}{player}",
        "{player}{item}{unknown}",
        "{player}{item}{",
        "x" * 513,
        "{player}{item}\n",
    ],
)
def test_invalid_translations_fall_back_without_injecting_markup(lua, template):
    translator(
        lua, {"gamma_ap_notice_received_item": template, "gamma_ap_reward_28051001": "%c[red]"}
    )
    notice = semantic()
    assert lua.globals().gamma_ap_notice_text.render(parsed(lua, notice)) == notice.text


@pytest.mark.parametrize(
    "mutation",
    [
        ("received_item", "unknown"),
        ("received_item", "sent_item"),
        ("|28051001\n", "|999\n"),
        ("|28051001\n", "|01\n"),
        ("7b6974656d7d", "25"),
        ("7b6974656d7d", "f"),
        ("7b6974656d7d", "a" * 770),
        ("|1|received", "|01|received"),
    ],
)
def test_semantic_malformed_records_never_reach_the_pda(lua, mutation):
    content = encode_notices(KEY, (semantic(),)).replace(*mutation)
    assert_lua_error(lua.globals().gamma_ap_notifications.parse(content, KEY))


def test_mixed_v2_legacy_and_semantic_display_waits_for_receipt_and_survives_reload(lua):
    game, engine = load_game(lua)
    lua.execute(
        "engine.news={}; db.actor.give_game_news=function(self,title,text) "
        "engine.news[#engine.news+1]=text end"
    )
    translator(lua, {"gamma_ap_notice_received_item": '{player}: "{item}".'})
    set_incoming(engine, items=(28051001,))
    engine.files["D:/AnomalyAP/appdata/archipelago\\notices.txt"] = encode_notices(
        KEY, (semantic(), Notice("s:3:2:5", 0, "Legacy transfer"))
    )
    game.actor_on_update()
    engine.now += 500
    game.actor_on_update()
    assert list(engine.news.values()) == ['{item}: "Basic Toolkit".', "Legacy transfer"]
    game.load_state(saved_state(lua, game))
    engine.now += 500
    game.actor_on_update()
    assert len(engine.news) == 2
