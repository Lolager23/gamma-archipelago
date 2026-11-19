import pytest

from gamma_archipelago.catalog import GAME
from gamma_archipelago.notice_causes import CAUSE_TEMPLATES, CheckCause
from gamma_archipelago.notice_text import CAUSAL_TEMPLATES
from gamma_archipelago.notifications import Notice, encode_notices, transfer_notice

from .assertions import assert_lua_error
from .test_game_adapter import enter_world, load_game, saved_state, set_incoming
from .test_notice_text import KEY, parsed, translator

DEFAULT_CAUSE = CheckCause("enter", "Rostok")


def notice(*, cause=DEFAULT_CAUSE, outgoing=False):
    return transfer_notice(
        "s:3:2:4" if outgoing else "r:0",
        0 if outgoing else 1,
        "Friend",
        "PDA",
        item_id=28051602,
        game=GAME,
        outgoing=outgoing,
        cause=cause,
    )


@pytest.mark.parametrize("kind", sorted(CAUSE_TEMPLATES))
@pytest.mark.parametrize("outgoing", [False, True])
def test_every_cause_roundtrips_and_matches_python_english(lua, kind, outgoing):
    message = notice(cause=CheckCause(kind, "{item} 15"), outgoing=outgoing)
    translator(lua, {})
    assert lua.globals().gamma_ap_notice_text.render(parsed(lua, message)) == message.text
    assert "{item}" in message.text


def test_causal_translation_reorders_fields_and_does_not_resubstitute_labels(lua):
    translator(
        lua,
        {
            "gamma_ap_notice_received_unlock_cause": '{cause}: {player}: "{item}".',
            "gamma_ap_cause_enter": "Entered {value}",
            "gamma_ap_reward_28051602": "Translated PDA",
        },
    )
    message = notice(cause=CheckCause("enter", "{player}"))
    assert lua.globals().gamma_ap_notice_text.render(parsed(lua, message)) == (
        'Entered {player}: Friend: "Translated PDA".'
    )


@pytest.mark.parametrize(
    "translation",
    ["", "{value}{value}", "{value}{unknown}", "{value}{", "{player}", "%c[red]{value}", "x" * 513],
)
def test_invalid_cause_translations_use_english_without_losing_the_cause(lua, translation):
    translator(
        lua,
        {
            "gamma_ap_cause_enter": translation,
            "gamma_ap_notice_received_unlock_cause": "{player}{item}",
        },
    )
    message = notice()
    assert lua.globals().gamma_ap_notice_text.render(parsed(lua, message)) == message.text


@pytest.mark.parametrize(
    "before,after",
    [
        ("|enter|", "|unknown|"),
        ("|enter|", "|none|"),
        ("526f73746f6b", ""),
        ("526f73746f6b", "f"),
        ("526f73746f6b", "25"),
        ("526f73746f6b", "a" * 770),
        ("|enter|526f73746f6b", ""),
        ("NOTICES|3", "NOTICES|4"),
        ("NOTICES|3", "NOTICES|03"),
    ],
)
def test_malformed_causal_records_are_rejected(lua, before, after):
    assert_lua_error(
        lua.globals().gamma_ap_notifications.parse(
            encode_notices(KEY, (notice(),)).replace(before, after), KEY
        )
    )


def test_v3_batches_can_mix_causal_plain_semantic_and_old_text(lua):
    messages = (
        notice(),
        transfer_notice("r:1", 2, "Friend", "Bandage", item_id=28051003, game=GAME, outgoing=False),
        Notice("s:1:2:5", 0, "Legacy text"),
    )
    decoded = lua.globals().gamma_ap_notifications.parse(encode_notices(KEY, messages), KEY)
    for index, message in enumerate(messages, 1):
        assert lua.globals().gamma_ap_notice_text.render(decoded[index]) == message.text
    assert CAUSAL_TEMPLATES["received_unlock"].endswith("{cause}.")


def test_cause_values_can_be_translated_without_renaming_foreign_check_labels(lua):
    from gamma_archipelago.notice_causes import value_key

    cause = CheckCause("enter", "Rostok")
    translator(
        lua,
        {
            value_key(cause): "Translated Rostok",
            value_key(CheckCause("check", "Rostok")): "Wrong namespace",
        },
    )
    assert (
        lua.globals()
        .gamma_ap_notice_text.render(parsed(lua, notice(cause=cause)))
        .endswith("by entering Translated Rostok.")
    )
    foreign = notice(cause=CheckCause("check", "Rostok"))
    assert (
        lua.globals()
        .gamma_ap_notice_text.render(parsed(lua, foreign))
        .endswith('by completing "Rostok".')
    )
    translator(lua, {value_key(cause): "%c[red]"})
    assert (
        lua.globals()
        .gamma_ap_notice_text.render(parsed(lua, notice(cause=cause)))
        .endswith("by entering Rostok.")
    )


def test_new_causes_do_not_replay_seen_rewards_or_bypass_load_readiness(lua):
    game, engine = load_game(lua)
    lua.execute(
        "engine.news={}; db.actor.give_game_news=function(self,title,text) "
        "engine.news[#engine.news+1]=text end"
    )
    old = transfer_notice(
        "r:0", 1, "Friend", "Basic Toolkit", item_id=28051001, game=GAME, outgoing=False
    )
    path = "D:/AnomalyAP/appdata/archipelago\\notices.txt"
    set_incoming(engine, items=(28051001,))
    engine.files[path] = encode_notices(KEY, (old,))
    game.actor_on_update()
    stored = saved_state(lua, game)
    new = transfer_notice(
        "r:1",
        2,
        "Friend",
        "Bandage",
        item_id=28051003,
        game=GAME,
        outgoing=False,
        cause=CheckCause("kill_total", "15"),
    )
    first_with_cause = transfer_notice(
        "r:0",
        1,
        "Friend",
        "Basic Toolkit",
        item_id=28051001,
        game=GAME,
        outgoing=False,
        cause=CheckCause("enter", "Cordon"),
    )
    set_incoming(engine, items=(28051001, 28051003))
    engine.files[path] = encode_notices(KEY, (first_with_cause, new))
    game.load_state(stored)
    engine.now += 500
    game.actor_on_update()
    assert list(engine.news.values()) == [old.text]
    enter_world(engine)
    engine.now += 500
    game.actor_on_update()
    assert list(engine.news.values()) == [old.text, new.text]
    assert len(engine.created) == 2
    game.load_state(saved_state(lua, game))
    enter_world(engine)
    engine.now += 500
    game.actor_on_update()
    assert len(engine.news) == 2 and len(engine.created) == 2
