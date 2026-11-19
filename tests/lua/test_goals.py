import pytest

from gamma_archipelago.catalog import MAP_LOCATION_IDS
from gamma_archipelago.protocol import decode_outgoing

from .test_game_adapter import saved_state
from .test_loadout import KEY
from .test_stashes import poll, progress, stash_game


def goal_game(lua, goal=1):
    game, engine = stash_game(lua, items=(), goal=goal)
    lua.execute("""
        db.actor.object=function(self,section)
            if engine.fail_protection then error('inventory failed') end
            if section=='good_psy_helmet' and engine.helmet_condition~=nil then
                return {condition=function() return engine.helmet_condition end}
            end
            return nil
        end
    """)
    return game, engine


def snapshot(engine):
    return decode_outgoing(
        engine.files["D:/AnomalyAP/appdata/archipelago\\outgoing.txt"],
        KEY,
        MAP_LOCATION_IDS,
        pilot_goal=False,
        configuration_key=engine.configuration_key,
    )


def test_psi_goal_needs_real_calibrated_usable_helmet_and_remains_complete_after_reload(lua):
    game, engine = goal_game(lua)
    poll(game, engine)
    assert not snapshot(engine).goal_complete
    engine.helmet_condition = 1
    poll(game, engine)
    assert snapshot(engine).goal_complete
    assert snapshot(engine).checked_locations == {28052001}
    game.load_state(saved_state(lua, game))
    engine.helmet_condition = None
    poll(game, engine)
    assert progress(lua, game).goal_complete and snapshot(engine).goal_complete


@pytest.mark.parametrize("condition", [0, -1, 1.1, True, float("nan"), "broken"])
def test_invalid_protection_does_not_complete_psi_goal(lua, condition):
    game, engine = goal_game(lua)
    engine.helmet_condition = condition
    poll(game, engine)
    assert not snapshot(engine).goal_complete


def test_goal_inventory_api_failure_is_visible_before_reporting_victory(lua):
    game, engine = goal_game(lua)
    engine.fail_protection = True
    poll(game, engine)
    assert not progress(lua, game).goal_complete
    assert "Cannot inspect" in list(engine.logs.values())[-1]


def test_brain_scorcher_goal_requires_native_shutdown_not_key_or_region_entry(lua):
    game, engine = goal_game(lua, goal=2)
    lua.execute("""has_alife_info=function(name) assert(name=='bar_deactivate_radar_done');
        return engine.shutdown end""")
    poll(game, engine)
    assert not snapshot(engine).goal_complete
    engine.shutdown = "true"
    poll(game, engine)
    assert not snapshot(engine).goal_complete
    engine.shutdown = True
    poll(game, engine)
    assert snapshot(engine).goal_complete
    game.load_state(saved_state(lua, game))
    engine.shutdown = False
    poll(game, engine)
    assert snapshot(engine).goal_complete


def test_unavailable_shutdown_api_does_not_report_victory(lua):
    game, engine = goal_game(lua, goal=2)
    poll(game, engine)
    assert not progress(lua, game).goal_complete
    assert "shutdown state" in list(engine.logs.values())[-1]
