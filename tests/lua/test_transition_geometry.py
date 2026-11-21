from .test_zone_keys import zone_game


def geometry(lua):
    game, engine = zone_game(lua)
    lua.execute("""
        engine.servers={};engine.changer_data={}
        local native=alife
        alife=function()
            local sim=native();sim.object=function(self,id) return engine.servers[id] end
            return sim
        end
        utils_stpk={get_level_changer_data=function(se) return engine.changer_data[se.id] end}
        server_changer=function(id,gvid,x,data)
            engine.servers[id]={id=id,m_game_vertex_id=gvid,position={x=x,y=0,z=0},
                clsid=function() return 95 end}
            engine.changer_data[id]=data
        end
    """)
    game.on_game_start()
    return engine


def test_unregistered_north_side_volume_and_reverse_arrival_prevent_reentry(lua):
    engine = geometry(lua)
    lua.execute("""
        -- Neither native trigger has entered db.storage yet.
        server_changer(50,0,100,{shapes={{shtype=0,offset={x=0,y=0,z=0},radius=30}}})
        server_changer(51,2,0,{shapes={},dest_game_vertex_id=1,dest_level_vertex_id=75,
            dest_position={x=-80,y=2,z=3}})
        engine.actor_position={x=110,y=2,z=3}
        db.actor.position=function() return engine.actor_position end
    """)
    packet = lua.globals().make_packet(2)
    lua.globals().CALifeUpdateManager__on_before_change_level(packet)
    assert packet.position.x == -80 and packet.lvid == 75
    areas, inverse = lua.globals().gamma_ap_transition_geometry.scan("l02_garbage")
    assert len(inverse) == 1
    module = lua.globals().gamma_ap_transition_geometry
    assert not module.outside(lua.table(x=100, y=100, z=0), areas)
    assert module.outside(packet.position, areas)
    assert engine.final_destination == 1


def test_overlapping_inverse_is_rejected_and_box_extent_is_conservative(lua):
    geometry(lua)
    lua.execute("""
        server_changer(50,0,100,{shapes={{shtype=1,offset={x=2,y=0,z=0},
            v1={x=10,y=0,z=0},v2={x=0,y=5,z=0},v3={x=0,y=0,z=10}}}})
        server_changer(51,2,0,{shapes={},dest_game_vertex_id=1,dest_level_vertex_id=75,
            dest_position={x=100,y=2,z=3}})
        engine.graph[4]='l01_escape';engine.points[4]={x=300,y=2,z=3}
        lc_extra_transitions={lc_pool={
            good={gvid='0',pos='-5, 0, 0',trigger_radius='20'},
            bad={gvid='0',pos='bad'},wrong={gvid='2',pos='0,0,0'},
            invalid={gvid='65535',pos='0,0,0'}}}
    """)
    packet = lua.globals().make_packet(2)
    lua.globals().CALifeUpdateManager__on_before_change_level(packet)
    assert packet.destination == 4 and packet.position.x == 300


def test_extra_transition_is_refused_before_dialog_or_travel_side_effects(lua):
    game, engine = zone_game(lua)
    lua.execute("""
        lc_extra_transitions={lc_pool={extra={to_gvid='3'}},
            handle_nearby_actor=function()
                engine.dialogs=(engine.dialogs or 0)+1;return 'shown' end}
        extra_object={section=function() return 'extra' end}
    """)
    game.on_game_start()
    extra = lua.globals().lc_extra_transitions
    assert extra.handle_nearby_actor(None, lua.globals().extra_object) is False
    assert engine.dialogs is None
    lua.globals().state = lua.globals().gamma_ap_state.new_state()
    lua.globals().gamma_ap_zone_keys.install(lua.eval("function() return state end"))
    assert extra.handle_nearby_actor(None, lua.globals().extra_object) == "shown"
