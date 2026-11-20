from .test_stashes import poll, progress, stash_game


def zone_game(lua, **options):
    game, engine = stash_game(lua, items=(28051702,), rewards_zone_keys=1, **options)
    lua.execute("""
        engine.travels=0; engine.packet_calls=0
        engine.graph={[0]='l01_escape',[1]='l01_escape',[2]='l02_garbage',[3]='l05_bar'}
        engine.points={[0]={x=1,y=2,z=3},[1]={x=100,y=2,z=3}}
        clsid={level_changer=94,level_changer_s=95}
        vector=function() return {set=function(self,x,y,z)
            self.x=x;self.y=y;self.z=z;return self end} end
        game_graph=function() return {
            valid_vertex_id=function(self,id) return engine.graph[id]~=nil end,
            vertex=function(self,id)
                return {level_id=function() return engine.graph[id] end,
                    level_point=function() return engine.points[id] end,
                    level_vertex_id=function() return id+10 end} end} end
        db.actor.game_vertex_id=function() return 1 end
        db.actor.level_vertex_id=function() return 10 end
        db.actor.position=function() return {x=1,y=2,z=3} end
        db.actor.direction=function() return {getH=function() return 0.5 end} end
        ChangeLevel=function(...) engine.travels=engine.travels+1;return 'native' end
        CALifeUpdateManager__on_before_change_level=function(packet)
            engine.packet_calls=engine.packet_calls+1
            engine.final_destination=packet:r_u16();packet:r_seek(2)
        end
        make_packet=function(gvid)
            return {destination=gvid,r_seek=function() end,
                r_u16=function(self) return self.destination end,
                w_begin=function(self,kind) assert(kind==13);self.vectors=0 end,
                w_u16=function(self,id) self.destination=id end,
                w_u32=function(self,id) self.lvid=id end,
                w_vec3=function(self,pos)
                    self.vectors=self.vectors+1
                    if self.vectors==1 then self.position=pos else self.heading=pos end
                end}
        end
    """)
    return game, engine


def test_locked_destination_is_stopped_in_scripts_and_redirected_before_native_packet_cleanup(lua):
    game, engine = zone_game(lua)
    game.on_game_start()
    packet = lua.globals().make_packet(2)
    lua.globals().CALifeUpdateManager__on_before_change_level(packet)
    assert engine.final_destination == 1 and packet.lvid == 11
    assert packet.position.x == 100 and packet.heading.y == 0.5
    assert lua.globals().ChangeLevel(None, 2, 2) is False
    poll(game, engine)
    assert progress(lua, game).received_count == 1
    # The second published key belongs to Garbage.
    assert progress(lua, game).unlocks.zone_l02_garbage
    assert lua.globals().ChangeLevel(None, 2, 2) == "native"
    packet = lua.globals().make_packet(2)
    lua.globals().CALifeUpdateManager__on_before_change_level(packet)
    assert engine.final_destination == 2
    assert lua.globals().ChangeLevel(None, 10, 1) == "native"
    assert lua.globals().ChangeLevel(None, 10, 999) is False
    packet = lua.globals().make_packet(999)
    lua.globals().CALifeUpdateManager__on_before_change_level(packet)
    assert engine.final_destination == 1


def test_non_cordon_start_and_missing_native_hooks_refuse_zone_seeds(lua):
    game, engine = zone_game(lua)
    lua.globals().ChangeLevel = None
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    assert "native transition" in list(engine.logs.values())[-1]
    lua.globals().ChangeLevel = lua.eval("function() end")
    engine.level_name = "l05_bar"
    # Test engine's level.name closure uses engine.current_level.
    lua.globals().level.name = lua.eval("function() return 'l05_bar' end")
    poll(game, engine)
    assert "Cordon start" in list(engine.logs.values())[-1]


def test_legacy_travel_passes_through_and_later_wrappers_preserve_delegation(lua):
    game, engine = zone_game(lua)
    module = lua.globals().gamma_ap_zone_keys
    state = lua.globals().gamma_ap_state.new_state()
    get_state = lua.eval("function(value) return function() return value end end")(state)
    assert module.install(get_state) is True
    assert lua.globals().ChangeLevel(None, 2, 999) == "native"
    lua.globals().CALifeUpdateManager__on_before_change_level(lua.globals().make_packet(999))
    assert engine.final_destination == 999
    lua.execute("""
        local original=ChangeLevel
        ChangeLevel=function(...) return original(...) end
        local packet_original=CALifeUpdateManager__on_before_change_level
        CALifeUpdateManager__on_before_change_level=function(...) return packet_original(...) end
    """)
    assert module.install(get_state) is True
    assert module.install(get_state) is True
    assert lua.globals().ChangeLevel(None, 2, 999) == "native"
    lua.globals().CALifeUpdateManager__on_before_change_level(lua.globals().make_packet(999))
    assert engine.packet_calls == 2


def test_online_changers_preserve_native_disabled_state_and_restore_only_ap_owned_flags(lua):
    game, engine = zone_game(lua)
    poll(game, engine)
    lua.execute("""
        db.storage={}; engine.changers={}
        -- Match the installed baseline: there is no IsLevelChanger global.
        isLc=function(obj) return obj:clsid()==94 end
        utils_stpk={get_level_changer_data=function(server)
            if engine.bad_changer then return nil end
            return {dest_game_vertex_id=server.destination}
        end}
        make_changer=function(id,name,active,target)
            local obj={active=active,clsid=function() return 94 end}
            obj.name=function() return name end
            obj.is_level_changer_enabled=function(self) return self.active end
            obj.enable_level_changer=function(self,value) self.active=value end
            db.storage[id]={object=obj}; engine.changers[id]=obj
            engine.servers[id]={destination=target}
            return obj
        end
    """)
    active = lua.globals().make_changer(200, "native-extra", True, 3)
    disabled = lua.globals().make_changer(201, "native-disabled", False, 2)
    poll(game, engine)
    assert not active.active and not disabled.active
    state = progress(lua, game)
    assert state.zone_disabled[200] == "native-extra"
    state.unlocks.zone_l05_bar = True
    assert lua.globals().gamma_ap_zone_keys.poll(state) is True
    assert active.active and not disabled.active
    # Reused ID with a different name loses AP ownership and stays native-disabled.
    state.zone_disabled[201] = "old-name"
    lua.globals().gamma_ap_zone_keys.poll(state)
    assert not state.zone_disabled[201] and not disabled.active
    engine.bad_changer = True
    assert lua.globals().gamma_ap_zone_keys.poll(state)[0] is False


def test_missing_transition_inspection_helpers_are_reported_without_blocking_key_delivery(lua):
    game, engine = zone_game(lua)
    lua.globals().db.storage = lua.table()
    poll(game, engine)
    assert progress(lua, game).received_count == 1
    assert "destination APIs" in list(engine.logs.values())[-1]
