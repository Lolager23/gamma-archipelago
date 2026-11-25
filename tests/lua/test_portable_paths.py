import pytest

from gamma_archipelago.installation import MARKER
from gamma_archipelago.protocol import decode_outgoing, encode_incoming

from .test_game_adapter import ITEMS, KEY, load_game, saved_state


def opener(lua, content, closed=True):
    factory = lua.eval("""function(content,closed)
        return function(path,mode)
            last_marker_path=path
            assert(mode=='rb')
            if content==false then return nil end
            return {read=function(_,limit) assert(limit==64);return content end,
                    close=function() return closed end}
        end
    end""")
    return factory(content, closed)


@pytest.mark.parametrize(
    "root,expected",
    [
        ("C:\\Games\\Stalker Anomaly\\appdata\\", "C:/Games/Stalker Anomaly/appdata/"),
        ("e:/Robert Cook/Anomaly/bin/../appdata", "E:/Robert Cook/Anomaly/appdata/"),
        ("F:/GAMMA User Data", "F:/GAMMA User Data/"),
        ("D:/Anomaly/appdata", "D:/Anomaly/appdata/"),
    ],
)
def test_explicitly_enrolled_generic_directories_are_canonicalized(lua, root, expected):
    paths = lua.globals().gamma_ap_paths
    assert paths.PORTABLE_MARKER == MARKER
    assert paths.appdata_root(root) is None
    assert paths.appdata_root(root, True) == expected
    assert paths.bridge_root(root, opener(lua, MARKER)) == expected
    assert lua.globals().last_marker_path == expected + "archipelago\\installation.txt"


@pytest.mark.parametrize(
    "content,closed", [(False, True), ("wrong", True), (MARKER + "extra", True), (MARKER, False)]
)
def test_non_dev_paths_require_a_complete_marker_and_successful_close(lua, content, closed):
    assert (
        lua.globals().gamma_ap_paths.bridge_root(
            "C:/Games/Anomaly/appdata", opener(lua, content, closed)
        )
        is None
    )


@pytest.mark.parametrize(
    "root",
    [
        "C:/",
        "C:/../Game",
        "relative/appdata",
        "\\\\server\\share",
        "C:/bad:stream/appdata",
        "C:/" + "x" * 4096,
    ],
)
def test_portable_selection_does_not_weaken_windows_path_validation(lua, root):
    paths = lua.globals().gamma_ap_paths
    assert paths.appdata_root(root, True) is None
    assert paths.bridge_root(root, opener(lua, MARKER)) is None


def test_native_adapter_receives_and_reports_in_a_registered_custom_installation(lua):
    game, engine = load_game(lua)
    from pathlib import Path

    loader = lua.globals().load_ap_module
    lua.globals().gamma_ap_actions = loader(
        str(Path(__file__).resolve().parents[2] / "mod/gamedata/scripts/gamma_ap_actions.script")
    )
    lua.globals().gamma_ap_actions.io = lua.globals().mock_io
    root = "C:/Games/Robert Cook/Anomaly/appdata/"
    engine.root = root
    engine.files[root + "archipelago\\installation.txt"] = MARKER
    engine.files[root + "archipelago\\incoming.txt"] = encode_incoming(KEY, ITEMS)
    game.actor_on_update()
    assert saved_state(lua, game).gamma_archipelago_v1.received_count == 1
    packet = engine.files[root + "archipelago\\outgoing.txt"]
    assert decode_outgoing(packet, KEY).received_count == 1
    assert lua.globals().gamma_ap_actions.can_spawn()
    assert engine.files["D:/AnomalyAP/appdata/archipelago\\outgoing.txt"] is None


def test_unregistered_custom_installation_does_not_deliver_or_write(lua):
    game, engine = load_game(lua)
    from pathlib import Path

    loader = lua.globals().load_ap_module
    lua.globals().gamma_ap_actions = loader(
        str(Path(__file__).resolve().parents[2] / "mod/gamedata/scripts/gamma_ap_actions.script")
    )
    lua.globals().gamma_ap_actions.io = lua.globals().mock_io
    root = "C:/Games/Anomaly/appdata/"
    engine.root = root
    engine.files[root + "archipelago\\incoming.txt"] = encode_incoming(KEY, ITEMS)
    game.actor_on_update()
    assert not list(engine.created.values())
    assert engine.files[root + "archipelago\\outgoing.txt"] is None
    assert not lua.globals().gamma_ap_actions.can_spawn()
