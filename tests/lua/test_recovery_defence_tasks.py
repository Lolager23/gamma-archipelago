"""GAMMA stash-retrieval and Flea Market task records must map to their checks."""

import pytest

from .test_tasks import emit, entry, progress, task_game

RECOVERY = 28052503
DEFENCE = 28052507
TASKS = (
    ("simulation_task_46", False, "drx_sl_quest_item_task_status", RECOVERY),
    ("simulation_task_46", False, "drx_sl_quest_item_task_target", RECOVERY),
    (
        "jup_a6_freedom_leader_task_freedom_intel_documents",
        False,
        "nta_stash_task_status_functor",
        RECOVERY,
    ),
    ("merc_pri_grifon_mlr_task_monolith_plans", False, "nta_stash_task_target_functor", RECOVERY),
    (
        "drx_sl_bar_dolg_general_petrenko_stalker_task_4",
        True,
        "drx_sl_retrieve_item_task_status",
        RECOVERY,
    ),
    (
        "bar_dolg_general_petrenko_stalker_task_hold_the_ground",
        False,
        "hold_the_ground_task_status_functor",
        DEFENCE,
    ),
    (
        "bar_dolg_general_petrenko_stalker_task_hold_the_ground",
        False,
        "hold_the_ground_task_target_functor",
        DEFENCE,
    ),
)


@pytest.mark.parametrize("task_id,storyline,functor,check", TASKS)
def test_native_stash_and_flea_market_completions_award_correct_type(
    lua, task_id, storyline, functor, check
):
    game, _, _ = task_game(lua, checks_quest_types=1)
    row = entry(lua, storyline=storyline, functor=functor)
    emit(lua, game, row, task_id)
    emit(lua, game, row, task_id)
    state = progress(lua, game)
    assert state.checks[check]
    assert not state.checks[28052501]  # Retrieval from a spawned stash is not a generic fetch.
    assert state.tasks.count == (0 if storyline else 1)
    game.load_state(lua.table(gamma_archipelago_v1=state))
    assert progress(lua, game).checks[check]
    emit(lua, game, row, task_id)
    assert progress(lua, game).tasks.count == (0 if storyline else 1)


@pytest.mark.parametrize(
    "check,functor",
    [(RECOVERY, "nta_stash_task_status_functor"), (DEFENCE, "hold_the_ground_task_status_functor")],
)
@pytest.mark.parametrize("reason", ("active", "failed", "cancelled", "forced_fail", "disabled"))
def test_native_task_mapping_still_requires_successful_enabled_completion(
    lua, check, functor, reason
):
    game, _, _ = task_game(lua, checks_quest_types=int(reason != "disabled"))
    row = entry(lua, functor=functor)
    row.cancelled_by_actor = reason == "cancelled"
    row.forced_status = "fail" if reason == "forced_fail" else None
    emit(lua, game, row, status={"active": 0, "failed": 2}.get(reason, 1))
    assert not progress(lua, game).checks[check]


def test_known_story_id_takes_precedence_over_recovery_exception(lua):
    game, _, _ = task_game(
        lua,
        checks_quest_types=1,
        checks_story_milestones=1,
        checks_mortal_sin=1,
        checks_operation_afterglow=1,
    )
    task_id, check = next(iter(lua.globals().gamma_ap_catalog.story_task_locations.items()))
    emit(lua, game, entry(lua, storyline=True, functor="drx_sl_retrieve_item_task_status"), task_id)
    state = progress(lua, game)
    assert state.checks[check] and not state.checks[RECOVERY]
    assert state.tasks.count == 0
