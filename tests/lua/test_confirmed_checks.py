import pytest

from gamma_archipelago.protocol import decode_outgoing, encode_confirmed

from .test_game_adapter import load_game, saved_state, set_incoming

KEY = "a" * 64
PATH = "D:/AnomalyAP/appdata/archipelago\\confirmed_checks.txt"


def test_server_confirmed_visits_survive_loading_a_save_without_those_visits(lua):
    game, engine = load_game(lua)
    set_incoming(engine)
    engine.files[PATH] = encode_confirmed(KEY, frozenset({28052002, 28052003}))
    game.actor_on_update()
    outgoing = engine.files["D:/AnomalyAP/appdata/archipelago\\outgoing.txt"]
    assert decode_outgoing(outgoing, KEY).goal_complete
    assert dict(saved_state(lua, game).gamma_archipelago_v1.checks) == {
        28052001: True,
        28052002: True,
        28052003: True,
    }


@pytest.mark.parametrize(
    "content",
    [
        None,
        "x" * 131073,
        "partial",
        "\n",
        "GAMMA_AP_CONFIRMED|1\n",
        encode_confirmed("b" * 64, frozenset()),
        encode_confirmed(KEY, frozenset()).replace("end|0", "end|01"),
        encode_confirmed(KEY, frozenset()).replace("end|0", "end|1"),
        f"GAMMA_AP_CONFIRMED|1\nsession|{KEY}\nend|4\n",
        f"GAMMA_AP_CONFIRMED|1\nsession|{KEY}\ncheck|99\nend|1\n",
        f"GAMMA_AP_CONFIRMED|1\nsession|{KEY}\ncheck|28052001\ncheck|28052001\nend|2\n",
    ],
)
def test_confirmed_packets_do_not_accept_partial_foreign_or_unknown_progress(lua, content):
    assert lua.globals().gamma_ap_protocol.parse_confirmed(content, KEY)[0] is None


def test_confirmed_read_failure_does_not_apply_pending_items(lua):
    game, engine = load_game(lua)
    set_incoming(engine)
    engine.files[PATH] = "invalid"
    game.actor_on_update()
    assert not list(engine.created.values())
    engine.now += 500
    engine.files[PATH] = encode_confirmed(KEY, frozenset())
    engine.fail_close = True
    game.actor_on_update()
    assert not list(engine.created.values())


def test_path_recheck_still_refuses_a_write_if_root_changes_after_read(lua):
    game, engine = load_game(lua)
    set_incoming(engine)
    engine.files[PATH] = encode_confirmed(KEY, frozenset())
    lua.execute("""
        local original = mock_io.open
        mock_io.open = function(path,mode)
            local file = original(path,mode)
            if path:find('confirmed_checks.txt', 1, true) then
                file.close = function() engine.root='D:/Anomaly/appdata/'; return true end
            end
            return file
        end
    """)
    game.actor_on_update()
    assert any("allowed only" in value for value in engine.logs.values())
