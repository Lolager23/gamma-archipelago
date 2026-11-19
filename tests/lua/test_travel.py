import pytest

from .test_game_adapter import saved_state
from .test_stashes import poll, progress
from .test_zone_keys import zone_game


def travel_game(lua):
    game, engine = zone_game(lua, zone_unlock_travel=1)
    lua.execute("""
        engine.travel_news={};engine.native_travel=2;engine.weight=10
        db.actor.give_game_news=function(self,title,message)
            engine.travel_news[#engine.travel_news+1]=message end
        db.actor.bleeding=0;db.actor.radiation=0
        db.actor.get_total_weight=function() return engine.weight end
        db.actor.get_actor_max_walk_weight=function() return 50 end
        ui_options={get=function() return engine.native_travel end}
        xr_combat_ignore={fighting_with_actor_npcs={}}
        xr_conditions={surge_started=function() return engine.surge end}
        psi_storm_manager={is_started=function() return engine.psi end}
        IsStalker=function(obj,class) return class=='stalker' end
        character_community=function() return 'actor_stalker' end
        game_relations={is_factions_enemies=function() return engine.hostile end}
        relation_registry={community_goodwill=function() return engine.personal or 0 end}
        local resident={clsid=function() return 'stalker' end,
            community=function() return 'stalker' end}
        engine.hub={id=1000,name=function() return 'esc_smart_terrain_2_12' end,
            npc_info={[501]={se_obj=resident}},m_game_vertex_id=1,m_level_vertex_id=10,
            position={x=10,y=0,z=10}}
        SIMBOARD={smarts_by_names={esc_smart_terrain_2_12=engine.hub}}
    """)
    poll(game, engine)
    return game, engine


def test_trip_requires_preview_then_consumes_once_and_survives_reload(lua):
    game, engine = travel_game(lua)
    assert game.take_unlock_travel() is False
    assert game.preview_unlock_travel() is True
    assert "Rookie Village" in list(engine.travel_news.values())[-1]
    assert engine.travels == 0
    assert game.take_unlock_travel() is True
    assert engine.travels == 1 and progress(lua, game).travel_used.l02_garbage
    game.load_state(saved_state(lua, game))
    assert game.preview_unlock_travel() is False
    assert game.take_unlock_travel() is False


@pytest.mark.parametrize(
    "hazard", ["native_travel", "weight", "surge", "psi", "combat", "bleeding"]
)
def test_native_hazards_block_without_consuming_entitlement(lua, hazard):
    game, engine = travel_game(lua)
    assert game.preview_unlock_travel() is True
    if hazard == "combat":
        lua.globals().xr_combat_ignore.fighting_with_actor_npcs[1] = True
    elif hazard == "bleeding":
        lua.globals().db.actor.bleeding = 0.1
    else:
        engine[hazard] = 0 if hazard == "native_travel" else 100
    assert game.take_unlock_travel() is False
    assert not progress(lua, game).travel_used.l02_garbage


def test_hostile_missing_changed_and_invalid_hubs_are_not_used(lua):
    game, engine = travel_game(lua)
    engine.hostile = True
    assert game.preview_unlock_travel() is False
    engine.hostile = False
    engine.personal = -1000
    assert game.preview_unlock_travel() is False
    engine.personal = 0
    assert game.preview_unlock_travel() is True
    engine.hub.npc_info = lua.table()
    assert game.take_unlock_travel() is False
    assert not progress(lua, game).travel_selection
    lua.globals().SIMBOARD = None
    assert game.preview_unlock_travel() is False
    lua.globals().gamma_ap_travel.preview(lua.globals().gamma_ap_state.new_state())


def test_online_hostility_bad_resident_and_coordinates_refuse_travel(lua):
    game, engine = travel_game(lua)
    engine.boxes[501] = lua.table(general_goodwill=lua.eval("function() return -1000 end"))
    assert game.preview_unlock_travel() is False
    engine.boxes[501] = None
    resident = engine.hub.npc_info[501].se_obj
    engine.hub.npc_info[501].se_obj = None
    assert game.preview_unlock_travel() is False
    engine.hub.npc_info[501].se_obj = resident
    engine.hub.m_game_vertex_id = 2
    assert game.preview_unlock_travel() is False
    engine.hub.m_game_vertex_id = 1
    assert game.preview_unlock_travel() is True
    engine.hub.m_level_vertex_id = -1
    assert game.take_unlock_travel() is False
    engine.hub.m_level_vertex_id = 10
    lua.globals().ui_options = None
    assert game.take_unlock_travel() is False


@pytest.mark.parametrize("result", ["false", "exception"])
def test_travel_failure_consumption_distinguishes_refusal_from_uncertain_side_effect(lua, result):
    game, engine = travel_game(lua)
    assert game.preview_unlock_travel() is True
    lua.globals().ChangeLevel = lua.eval(
        "function() return false end"
        if result == "false"
        else "function() error('after travel') end"
    )
    assert game.take_unlock_travel() is False
    assert bool(progress(lua, game).travel_used.l02_garbage) == (result == "exception")


def test_preview_uses_native_settlement_translation_with_a_readable_fallback(lua):
    game, engine = travel_game(lua)
    lua.globals().game = lua.table(
        translate_string=lua.eval("function() return 'Localized village' end")
    )
    assert game.preview_unlock_travel() is True
    assert "Localized village" in list(engine.travel_news.values())[-1]
    lua.globals().game.translate_string = lua.eval("function(name) return name end")
    assert game.preview_unlock_travel() is True
    assert "Rookie Village" in list(engine.travel_news.values())[-1]


@pytest.mark.parametrize("vertex", [1.5, float("nan"), "10"])
def test_invalid_settlement_vertex_refuses_travel_without_consuming_the_key_trip(lua, vertex):
    game, engine = travel_game(lua)
    engine.hub.m_level_vertex_id = vertex
    assert game.preview_unlock_travel() is True
    assert game.take_unlock_travel() is False
    assert engine.travels == 0
    assert not progress(lua, game).travel_used.l02_garbage
