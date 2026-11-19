from pathlib import Path

from gamma_archipelago.catalog import ITEM_SECTIONS
from gamma_archipelago.protocol import decode_outgoing, encode_incoming

KEY = "a" * 64
ITEMS = tuple(ITEM_SECTIONS)
ROOT = Path(__file__).resolve().parents[2]


def load_game(lua):
    lua.execute(
        """
        engine = {now=1000, root="D:/AnomalyAP/appdata/", alive=true, level="l01_escape",
                  files={}, logs={}, created={}, callbacks={}, fail_open=false,
                  fail_write=false, fail_close=false, fail_reward=false}
        db = {actor={alive=function() return engine.alive end}}
        time_global = function() return engine.now end
        level = {name=function() return engine.level end}
        getFS = function() return {update_path=function() return engine.root end} end
        printf = function(format, value) engine.logs[#engine.logs+1]=string.format(format,value) end
        RegisterScriptCallback = function(name,callback) engine.callbacks[name]=callback end
        alife_create_item = function(section,actor)
            if engine.fail_reward then return nil end
            engine.created[#engine.created+1]=section
            return {id=1}
        end
        mock_io = {open=function(path,mode)
            if engine.fail_open and mode=="wb" then return nil,"denied" end
            if mode=="rb" and not engine.files[path] then return nil end
            return {
                read=function() return engine.files[path] end,
                write=function(self,text)
                    if engine.fail_write then return nil end
                    engine.files[path]=text
                    return self
                end,
                close=function() return not engine.fail_close end
            }
        end}
        """
    )
    module = lua.globals().load_ap_module(str(ROOT / "mod/gamedata/scripts/gamma_ap_game.script"))
    module.io = lua.globals().mock_io
    lua.globals().gamma_ap_notifications.io = lua.globals().mock_io
    module.on_game_start()
    return module, lua.globals().engine


def set_incoming(engine, items=ITEMS, key=KEY):
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = encode_incoming(key, items)


def saved_state(lua, module):
    data = lua.table()
    module.save_state(data)
    return data


def test_callbacks_polling_save_restore_and_initial_inventory(lua):
    module, engine = load_game(lua)
    assert set(engine.callbacks.keys()) == {
        "actor_on_update",
        "save_state",
        "load_state",
        "actor_on_interaction",
        "npc_on_death_callback",
        "monster_on_death_callback",
        "monster_on_hit_callback",
        "npc_on_net_spawn",
        "monster_on_net_spawn",
    }
    set_incoming(engine)
    module.actor_on_update()
    module.actor_on_update()
    assert list(engine.created.values()) == ["itm_basickit"]
    stored = saved_state(lua, module)
    engine.now = 2000
    engine.level = "l02_garbage"
    module.actor_on_update()
    assert list(engine.created.values()) == ["itm_basickit", "medkit"]
    module.load_state(stored)
    module.actor_on_update()
    assert list(engine.created.values()) == ["itm_basickit", "medkit", "medkit"]
    assert stored.gamma_archipelago_v1.received_count == 1
    packet = engine.files["D:/AnomalyAP/appdata/archipelago\\outgoing.txt"]
    assert decode_outgoing(packet, KEY).received_count == 2


def test_missing_or_dead_actor_is_ignored_and_new_game_resets(lua):
    module, engine = load_game(lua)
    set_incoming(engine)
    engine.alive = False
    module.actor_on_update()
    engine.alive = True
    actor = lua.globals().db.actor
    lua.globals().db.actor = None
    module.actor_on_update()
    lua.globals().db.actor = actor
    module.actor_on_update()
    assert saved_state(lua, module).gamma_archipelago_v1.received_count == 1
    module.load_state(lua.table())
    assert saved_state(lua, module).gamma_archipelago_v1.received_count == 0
    module.on_game_start()
    assert saved_state(lua, module).gamma_archipelago_v1.session_key is None


def test_original_installation_is_refused_without_file_access(lua):
    module, engine = load_game(lua)
    engine.root = "D:/Anomaly/appdata/"
    module.actor_on_update()
    assert "allowed only" in list(engine.logs.values())[-1]
    assert not list(engine.created.values())
    # Reach write-path denial after a successful read to cover both boundaries.
    engine.now += 1000
    set_incoming(engine)
    engine.root = "D:/AnomalyAP/appdata/"
    module.load_state(lua.table())
    lua.execute(
        "getFS=function() local saved=engine.root; "
        "engine.root='D:/Anomaly/appdata/'; return {update_path=function() return saved end} end"
    )
    module.actor_on_update()
    assert "allowed only" in list(engine.logs.values())[-1]


def test_missing_file_malformed_input_and_duplicate_error_are_bounded(lua):
    module, engine = load_game(lua)
    module.actor_on_update()
    initial = len(engine.logs)
    engine.now += 1000
    module.actor_on_update()
    assert len(engine.logs) == initial
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = "broken\n"
    engine.now += 1000
    module.actor_on_update()
    assert "protocol" in list(engine.logs.values())[-1].lower()


def test_reward_failures_and_session_mismatch_are_reported(lua):
    module, engine = load_game(lua)
    set_incoming(engine)
    engine.fail_reward = True
    module.actor_on_update()
    assert saved_state(lua, module).gamma_archipelago_v1.received_count == 0
    assert "Reward creation failed" in list(engine.logs.values())[-1]
    engine.now += 1000
    engine.fail_reward = False
    module.actor_on_update()
    set_incoming(engine, key="b" * 64)
    engine.now += 1000
    module.actor_on_update()
    assert "another AP seed" in list(engine.logs.values())[-1]


def test_write_open_write_and_close_failures_are_reported(lua):
    module, engine = load_game(lua)
    set_incoming(engine)
    for failure in ("fail_open", "fail_write", "fail_close"):
        engine[failure] = True
        engine.now += 1000
        module.actor_on_update()
        assert any("write" in message or "failed" in message for message in engine.logs.values())
        engine[failure] = False


def test_bridge_accepts_the_engine_bin_parent_alias_without_writing_outside_appdata(lua):
    module, engine = load_game(lua)
    engine.root = "d:/anomalyap/bin/..\\appdata\\"
    set_incoming(engine)
    module.actor_on_update()
    assert list(engine.created.values()) == ["itm_basickit"]
    assert "D:/AnomalyAP/appdata/archipelago\\outgoing.txt" in engine.files
