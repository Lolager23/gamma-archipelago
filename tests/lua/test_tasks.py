import pytest

from gamma_archipelago.catalog import SIDE_TASK_MILESTONE_BASE, enabled_location_ids
from gamma_archipelago.configuration import encode_configuration
from gamma_archipelago.protocol import encode_confirmed

from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, KEY, configured_game


def task_game(lua, **options):
    lua.execute("""
        callbacks_gameobject={task_callback=function() end}
        task={completed=1,fail=2}
        task_manager={task_ini={r_string_ex=function(self,id,key) return task_parameters end}}
    """)
    game, engine, configuration = configured_game(
        lua, checks_maps=0, checks_side_task_milestones=1, side_task_milestones=[1, 2, 4], **options
    )
    lua.execute("db.actor.has_info=function(self,key) return engine.story_disabled or false end")
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    game.actor_on_update()
    return game, engine, configuration


def entry(lua, *, time=1, storyline=False, functor="actor_has_fetch_item"):
    return lua.table(
        storyline=storyline,
        status_functor=functor,
        inited_time=lua.eval(
            "function(value) return {get=function() return 2018,1,2,3,4,5,value end} end"
        )(time),
    )


def emit(lua, game, row, id_="repeat_task", *, status=1):
    object_ = lua.eval("function(id) return {get_id=function() return id end} end")(id_)
    manager = lua.table(task_info=lua.table())
    manager.task_info[id_] = row
    game.actor_on_task_callback(object_, status, manager, id_)


def progress(lua, game):
    return saved_state(lua, game).gamma_archipelago_v1


def test_repeat_template_instances_deduplicate_save_and_restore_their_counter(lua):
    game, _, configuration = task_game(lua, checks_quest_types=1)
    first = entry(lua)
    emit(lua, game, first)
    emit(lua, game, first)
    earlier = saved_state(lua, game)
    emit(lua, game, entry(lua, time=2))
    assert progress(lua, game).tasks.count == 2
    assert progress(lua, game).checks[SIDE_TASK_MILESTONE_BASE + 2]
    assert earlier.gamma_archipelago_v1.tasks.count == 1
    game.load_state(earlier)
    emit(lua, game, first)
    assert progress(lua, game).tasks.count == 1
    for time in range(2, 9):
        emit(lua, game, entry(lua, time=time))
    state = progress(lua, game)
    assert state.tasks.count == 4 and len(list(state.tasks.seen)) == 4
    allowed = enabled_location_ids(
        configuration.checks, configuration.kill_milestones, configuration.side_task_milestones
    )
    assert set(state.enabled_checks) == allowed
    packet = encode_confirmed(KEY, frozenset({SIDE_TASK_MILESTONE_BASE + 4}))
    assert lua.globals().gamma_ap_protocol.parse_confirmed(packet, KEY)[
        SIDE_TASK_MILESTONE_BASE + 4
    ]


def test_all_task_functors_and_monster_assault_normalize_to_the_finite_roster(lua):
    game, _, _ = task_game(lua, checks_quest_types=1)
    catalogue = lua.globals().gamma_ap_catalog
    for index, (functor, name) in enumerate(catalogue.task_functors.items(), 1):
        row = entry(lua, time=index, functor=functor)
        emit(lua, game, row)
        assert progress(lua, game).checks[catalogue.quest_type_locations[name]]
    # Exercise target/title fallback rather than substring guessing.
    for field in ("target_functor", "title_functor"):
        row = entry(lua, functor="unknown")
        row[field] = "general_fetch_task"
        emit(lua, game, row)
    lua.globals().task_parameters = "monster, monster_predatory_day"
    emit(lua, game, entry(lua, functor="assault_task_status_functor"))
    assert progress(lua, game).checks[catalogue.quest_type_locations.hunting]
    emit(lua, game, entry(lua, functor="unknown"))


def test_story_variants_share_checks_and_never_increment_side_totals(lua):
    game, _, _ = task_game(
        lua, checks_story_milestones=1, checks_mortal_sin=1, checks_operation_afterglow=1
    )
    catalogue = lua.globals().gamma_ap_catalog
    for id_, location in catalogue.story_task_locations.items():
        emit(lua, game, entry(lua, storyline=True), id_)
        emit(lua, game, entry(lua, storyline=True), id_)
        assert progress(lua, game).checks[location]
    state = progress(lua, game)
    assert len(list(state.checks)) == len(list(state.tasks.stories)) == 53
    assert state.tasks.count == 0
    game.load_state(lua.table(gamma_archipelago_v1=state))
    assert len(list(progress(lua, game).tasks.stories)) == 53
    emit(lua, game, entry(lua, storyline=True), "unmapped_story")
    emit(lua, game, entry(lua, storyline=None), "missing_story_flag")
    assert progress(lua, game).tasks.count == 0


def test_failed_cancelled_and_missing_tasks_cannot_supply_checks(lua):
    game, _, _ = task_game(lua)
    emit(lua, game, entry(lua), status=2)
    emit(lua, game, entry(lua), status=3)
    row = entry(lua)
    row.cancelled_by_actor = True
    emit(lua, game, row)
    row.cancelled_by_actor = False
    row.forced_status = "fail"
    emit(lua, game, row)
    emit(lua, game, None)
    game.actor_on_task_callback(lua.table(get_id=lambda *_: "x"), 1, None, "x")
    assert progress(lua, game).tasks.count == 0


@pytest.mark.parametrize("time", [None, -1, 1.5, float("nan"), float("inf"), "1"])
def test_missing_or_invalid_instance_time_is_refused_without_counting(lua, time):
    game, engine, _ = task_game(lua)
    row = entry(lua, time=time)
    if time is None:
        row.inited_time = None
    emit(lua, game, row)
    assert progress(lua, game).tasks.count == 0
    assert "valid saved instance time" in list(engine.logs.values())[-1]


def test_identity_dead_actor_legacy_and_unbound_guards(lua):
    game, engine, _ = task_game(lua)
    for object_, id_ in (
        (None, "x"),
        (lua.table(get_id=lambda *_: "different"), "x"),
        (lua.table(), "x" * 129),
        (lua.table(), 1),
    ):
        game.actor_on_task_callback(object_, 1, None, id_)
    assert "identity is invalid" in list(engine.logs.values())[-1]
    engine.alive = False
    emit(lua, game, entry(lua))
    engine.alive = True
    actor = lua.globals().db.actor
    lua.globals().db.actor = None
    emit(lua, game, entry(lua))
    lua.globals().db.actor = actor
    state = lua.globals().gamma_ap_state.new_state()
    assert lua.globals().gamma_ap_tasks.observe(state, None, 1, None, None) is True
    state.session_key = KEY
    assert lua.globals().gamma_ap_tasks.observe(state, None, 1, None, None) is True
    assert progress(lua, game).tasks.count == 0


def test_hook_requirement_late_registration_and_story_mode_refusal(lua):
    game, engine, _ = task_game(
        lua, checks_story_milestones=1, checks_mortal_sin=1, checks_operation_afterglow=1
    )
    assert engine.callbacks.actor_on_task_callback is not None
    lua.globals().callbacks_gameobject = None
    engine.now += 1000
    game.actor_on_update()
    assert "Monolith task hook" in list(engine.logs.values())[-1]
    lua.globals().callbacks_gameobject = lua.table(task_callback=True)
    assert lua.globals().gamma_ap_tasks.hook_available() is False
    lua.execute("callbacks_gameobject={task_callback=function()end}")
    engine.story_disabled = True
    engine.now += 1000
    game.actor_on_update()
    assert "story mode enabled" in list(engine.logs.values())[-1]
    engine.story_disabled = False
    lua.globals().callbacks_gameobject = None
    game.on_game_start()
    engine.callbacks.actor_on_task_callback = None
    lua.execute("callbacks_gameobject={task_callback=function()end}")
    engine.now += 1000
    game.actor_on_update()
    assert engine.callbacks.actor_on_task_callback is not None


def test_story_observation_is_retained_when_story_checks_are_disabled(lua):
    game, _, _ = task_game(lua)
    id_, location = next(iter(lua.globals().gamma_ap_catalog.story_task_locations.items()))
    emit(lua, game, entry(lua, storyline=True), id_)
    state = progress(lua, game)
    assert state.tasks.stories[location] and not state.checks[location]
