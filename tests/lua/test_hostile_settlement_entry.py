"""Physical settlement entry is evidence even outside AP's safe placement model."""

import pytest

from .test_game_adapter import saved_state
from .test_settlement_access import configured
from .test_settlements import smart


@pytest.mark.parametrize(
    "name,level,id",
    [
        ("esc_smart_terrain_3_16", "l01_escape", 28052103),
        ("agr_smart_terrain_1_6", "l03_agroprom", 28052106),
        ("val_smart_terrain_7_4", "l04_darkvalley", 28052108),
        ("cit_killers", "l09_deadcity", 28052112),
        ("red_smart_terrain_3_2", "l10_red_forest", 28052113),
        ("pri_monolith", "l11_pripyat", 28052114),
    ],
)
@pytest.mark.parametrize("goodwill", [-3000, 0, 1000, 1001, 1250])
def test_actual_hostile_entry_completes_once_without_goodwill_rewards_and_survives_reload(
    lua, name, level, id, goodwill
):
    game, engine, _ = configured(lua)
    engine.level = level
    lua.globals().goodwill = goodwill
    for _ in range(2):
        game.actor_on_interaction("smarts", smart(lua, name), name)
    saved = saved_state(lua, game)
    assert set(saved.gamma_archipelago_v1.checks) == {id}
    assert not list(lua.globals().queries)
    game.load_state(saved)
    assert set(saved_state(lua, game).gamma_archipelago_v1.checks) == {id}


@pytest.mark.parametrize("failure", ["missing", "setter", "identity"])
def test_reputation_floor_failure_cannot_suppress_an_actual_entry(lua, failure):
    game, engine, state = configured(lua)
    engine.level = "l09_deadcity"
    state.applied_items = lua.table_from([28051306] * 5)
    if failure == "missing":
        lua.globals().relation_registry = None
    elif failure == "setter":
        lua.execute("relation_registry.set_community_goodwill=function() error('unavailable') end")
    else:
        lua.execute("db.actor.id=function() return -1 end")
    received_before = state.received_count
    name = "cit_killers"
    game.actor_on_interaction("smarts", smart(lua, name), name)
    assert saved_state(lua, game).gamma_archipelago_v1.checks[28052112]
    assert state.received_count == received_before
