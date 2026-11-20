import pytest
from lupa.luajit21 import LuaError

from .test_stashes import poll, progress
from .test_zone_keys import zone_game


def test_silent_native_trigger_recovers_once_instead_of_reloading_inside_it(lua):
    game, engine = zone_game(lua)
    game.on_game_start()
    lua.execute("""
        engine.actor_position={x=1,y=2,z=3}
        db.actor.position=function() return engine.actor_position end
        -- Silent native changers ignore enable_level_changer(false).
        db.storage={[50]={object={clsid=function() return 95 end,
            inside=function(self,pos,radius) return pos.x<40+radius end}}}
        native_touch=function()
            if db.storage[50].object:inside(db.actor:position(),0) then
                local packet=make_packet(3)
                CALifeUpdateManager__on_before_change_level(packet)
                engine.actor_position=packet.position
                return true
            end
            return false
        end
    """)
    assert lua.globals().native_touch() is True
    assert engine.final_destination == 1
    assert lua.globals().native_touch() is False
    # Recovery uses graph geometry, so it also works without a cached pre-save point.
    lua.execute("engine.actor_position={x=1,y=2,z=3}")
    assert lua.globals().native_touch() is True
    assert lua.globals().native_touch() is False


def test_recovery_rejects_nearby_trigger_volumes_and_extra_transition_radii(lua):
    game, engine = zone_game(lua)
    game.on_game_start()
    lua.execute("""
        engine.graph[4]='l01_escape'; engine.points[4]={x=200,y=2,z=3}
        engine.graph[5]='l01_escape'; engine.points[5]={x=300,y=2,z=3}
        engine.graph[6]='l01_escape'; engine.points[6]={x=400,y=2,z=3}
        lc_extra_transitions={lc_pool={extra={trigger_radius='12'}}}
        db.storage={
            [1]={object={clsid=function() return 94 end,
                inside=function(self,pos,radius) return pos.x==100 and radius==10 end}},
            [2]={object={clsid=function() return 139 end,section=function() return 'extra' end,
                position=function() return {x=200,y=2,z=3} end}},
            [3]={object={clsid=function() return 139 end,
                section=function() return 'irrelevant' end}},
            [4]={}}
    """)
    packet = lua.globals().make_packet(3)
    lua.globals().CALifeUpdateManager__on_before_change_level(packet)
    assert packet.destination == 5 and packet.position.x == 300
    # No usable source vertex must never forward a locked target or the origin.
    lua.execute("engine.points[5]={x=1,y=2,z=3}; engine.points[6]={x=1,y=2,z=3}")
    with pytest.raises(LuaError, match="load an earlier save"):
        lua.globals().CALifeUpdateManager__on_before_change_level(lua.globals().make_packet(3))
    assert engine.packet_calls == 1


def test_late_script_and_extra_mod_guards_run_before_travel_side_effects(lua):
    game, engine = zone_game(lua)
    lua.execute("""
        change_level_now=function(...) engine.immediate=(engine.immediate or 0)+1;return 'now' end
        lc_extra_transitions={lc_pool={locked={to_gvid='3'},open={to_gvid='2'}}}
        lc_extra_transitions.teleport_actor=function(...)
            engine.extra=(engine.extra or 0)+1;return 'extra'
        end
        transition_object=function(section) return {section=function() return section end} end
    """)
    game.on_game_start()
    extra = lua.globals().lc_extra_transitions
    obj = lua.globals().transition_object
    assert extra.teleport_actor(None, obj("locked")) is False
    assert extra.teleport_actor(None, None) is False
    assert extra.teleport_actor(None, obj("unknown")) is False
    assert lua.globals().change_level_now(None, 0, 3) is False
    assert lua.globals().change_level_now(None, 0, None) is False
    assert engine.extra is None and engine.immediate is None
    poll(game, engine)
    assert extra.teleport_actor(None, obj("open")) == "extra"
    assert lua.globals().change_level_now(None, 0, 2) == "now"
    state = progress(lua, game)
    state.configuration.options.rewards_zone_keys = 0
    reader = lua.eval("function(state) return function() return state end end")(state)
    lua.globals().gamma_ap_zone_keys.install(reader)
    assert extra.teleport_actor(None, None) == "extra"


def test_spawn_guard_waits_for_loaded_permissions_and_preserves_native_result(lua):
    game, engine = zone_game(lua)
    lua.execute("""
        engine.active=true; engine.spawn_result=true
        bind_level_changer={lchanger_binder={net_spawn=function(self,...)
            engine.spawn_calls=engine.spawn_calls+1; return engine.spawn_result
        end}}
        utils_stpk={get_level_changer_data=function() return {dest_game_vertex_id=3} end}
        engine.binder={object={id=function() return 50 end,name=function() return 'changer' end,
            is_level_changer_enabled=function() return engine.active end,
            enable_level_changer=function(self,value) engine.active=value end}}
    """)
    game.on_game_start()
    binder = lua.globals().bind_level_changer.lchanger_binder
    assert binder.net_spawn(engine.binder) is True
    assert engine.active  # No loaded session yet: do not lose disable ownership on load_state.
    poll(game, engine)
    assert binder.net_spawn(engine.binder) is True
    assert not engine.active
    assert progress(lua, game).zone_disabled[50] == "changer"
    engine.spawn_result = False
    assert binder.net_spawn(engine.binder) is False
    engine.spawn_result = True
    lua.globals().utils_stpk = None
    assert binder.net_spawn(engine.binder) is True
    assert "destination APIs" in list(engine.logs.values())[-1]
