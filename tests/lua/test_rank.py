import pytest

from gamma_archipelago.configuration import encode_configuration

from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, KEY, configured_game


def rank_game(lua):
    game, engine, configuration = configured_game(lua, checks_maps=0, checks_rank_milestones=1)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    lua.execute("""
        engine.rank=0
        db.actor.character_rank=function()
            if engine.rank_error then error('rank API failed') end
            return engine.rank
        end
        ranks={get_rank_interval=function(name)
            if engine.interval_error then error('interval API failed') end
            for _,definition in ipairs(gamma_ap_catalog.rank_locations) do
                if definition.name==name then return {definition.minimum, 100000} end
            end
        end}
    """)
    return game, engine


def progress(lua, game):
    return saved_state(lua, game).gamma_archipelago_v1


def poll(game, engine):
    engine.now += 1000
    game.actor_on_update()


def test_each_active_rank_boundary_and_saved_high_water_mark(lua):
    game, engine = rank_game(lua)
    catalogue = lua.globals().gamma_ap_catalog
    for definition in sorted(catalogue.rank_locations.values(), key=lambda row: row.minimum):
        if definition.minimum > 0:
            engine.rank = definition.minimum - 1
            poll(game, engine)
            assert progress(lua, game).checks[definition.id] is None
        engine.rank = definition.minimum
        poll(game, engine)
        assert progress(lua, game).checks[definition.id] is True
        poll(game, engine)
    saved = saved_state(lua, game)
    assert len(list(saved.gamma_archipelago_v1.checks)) == 8
    engine.rank = 0
    poll(game, engine)
    assert progress(lua, game).rank_highest == 49999
    game.load_state(saved)
    poll(game, engine)
    assert len(list(progress(lua, game).checks)) == 8
    assert saved.gamma_archipelago_v1.rank_highest == 49999


def test_unsupported_thresholds_or_missing_module_refuse_before_reward_creation(lua):
    game, engine = rank_game(lua)
    lua.globals().ranks = None
    poll(game, engine)
    assert "rank interval API" in list(engine.logs.values())[-1]
    assert progress(lua, game).received_count == 0
    lua.globals().ranks = lua.table(get_rank_interval=False)
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    lua.execute("ranks={get_rank_interval=function() return {4000,6000} end}")
    poll(game, engine)
    assert "thresholds differ" in list(engine.logs.values())[-1]
    for result in (None, 1, "invalid"):
        lua.globals().ranks.get_rank_interval = lua.eval(
            "function(value) return function() return value end end"
        )(result)
        poll(game, engine)
        assert progress(lua, game).received_count == 0


@pytest.mark.parametrize("rank", [None, -1, 1.5, float("nan"), float("inf"), 2147483648, "100"])
def test_invalid_actor_rank_is_reported_without_progress(lua, rank):
    game, engine = rank_game(lua)
    engine.rank = rank
    poll(game, engine)
    assert "valid actor rank" in list(engine.logs.values())[-1]
    assert progress(lua, game).rank_highest == -1
    assert not list(progress(lua, game).checks)


def test_rank_and_interval_api_exceptions_are_retriable(lua):
    game, engine = rank_game(lua)
    engine.interval_error = True
    poll(game, engine)
    assert "thresholds differ" in list(engine.logs.values())[-1]
    engine.interval_error = False
    engine.rank_error = True
    poll(game, engine)
    assert "valid actor rank" in list(engine.logs.values())[-1]
    engine.rank_error = False
    poll(game, engine)
    assert progress(lua, game).checks[28052801]


def test_legacy_unbound_and_disabled_categories_do_not_query_rank(lua):
    module = lua.globals().gamma_ap_rank
    state = lua.globals().gamma_ap_state.new_state()
    assert module.poll(state, None) is True
    state.session_key = KEY
    assert module.poll(state, None) is True
    state.expanded = True
    assert module.poll(state, None) is True
    assert module.poll(state, lua.table(expanded=False)) is True
    assert (
        module.poll(state, lua.table(expanded=True, options=lua.table(checks_rank_milestones=0)))
        is True
    )
