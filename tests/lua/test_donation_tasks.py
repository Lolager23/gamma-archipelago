"""Native faction-payment tasks carry a storyline flag despite supplying Donation."""

import pytest

from .test_tasks import emit, entry, progress, task_game

DONATION_TASKS = (
    "drx_sl_agr_smart_terrain_1_6_near_2_military_colonel_kovalski_cf_task_1",
    "drx_sl_bar_dolg_general_petrenko_stalker_cf_task_1",
    "drx_sl_zat_b7_bandit_boss_sultan_cf_task_1",
    "drx_sl_cit_killers_merc_trader_stalker_cf_task_1",
    "drx_sl_esc_m_trader_cf_task_1",
    "drx_sl_mar_smart_terrain_base_stalker_leader_marsh_cf_task_1",
    "drx_sl_mil_smart_terrain_7_7_freedom_leader_stalker_cf_task_1",
    "drx_sl_pri_monolith_monolith_trader_stalker_cf_task_1",
    "drx_sl_red_greh_trader_cf_task_1",
    "drx_sl_yan_stalker_sakharov_cf_task_1",
)
DONATION = 28052511


@pytest.mark.parametrize("task_id", DONATION_TASKS)
def test_native_storyline_payment_completes_donation_without_side_job_credit(lua, task_id):
    game, _, _ = task_game(lua, checks_quest_types=1)
    payment = entry(lua, storyline=True, functor="drx_sl_money_task_status")
    emit(lua, game, payment, task_id)
    emit(lua, game, payment, task_id)
    state = progress(lua, game)
    assert state.checks[DONATION]
    assert state.tasks.count == 0 and not list(state.tasks.seen)
    game.load_state(lua.table(gamma_archipelago_v1=state))
    assert progress(lua, game).checks[DONATION]


def test_payment_target_fallback_and_nonstory_side_job_behavior(lua):
    game, _, _ = task_game(lua, checks_quest_types=1)
    payment = entry(lua, storyline=True, functor="unknown")
    payment.target_functor = "drx_sl_money_task_target"
    emit(lua, game, payment)
    assert progress(lua, game).checks[DONATION]
    assert progress(lua, game).tasks.count == 0
    emit(lua, game, entry(lua, functor="drx_sl_money_task_status"))
    assert progress(lua, game).tasks.count == 1


@pytest.mark.parametrize(
    "rejection",
    (
        "disabled",
        "active",
        "failed",
        "cancelled",
        "forced_fail",
        "no_flag",
        "story_alias",
        "other_story",
    ),
)
def test_payment_exception_preserves_completion_and_story_guards(lua, rejection):
    game, _, _ = task_game(lua, checks_quest_types=int(rejection != "disabled"))
    payment = entry(lua, storyline=True, functor="drx_sl_money_task_status")
    task_id = DONATION_TASKS[0]
    status = 1
    if rejection == "active":
        status = 0
    elif rejection == "failed":
        status = 2
    elif rejection == "cancelled":
        payment.cancelled_by_actor = True
    elif rejection == "forced_fail":
        payment.forced_status = "fail"
    elif rejection == "no_flag":
        payment.storyline = None
    elif rejection == "story_alias":
        task_id = next(iter(lua.globals().gamma_ap_catalog.story_task_locations))
    elif rejection == "other_story":
        payment.status_functor = "actor_has_fetch_item"
    emit(lua, game, payment, task_id, status=status)
    state = progress(lua, game)
    assert not state.checks[DONATION]
    assert state.tasks.count == 0 and not list(state.tasks.seen)
    if rejection == "other_story":
        assert not list(state.checks)
