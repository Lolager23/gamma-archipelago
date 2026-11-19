import pytest

from .test_game_adapter import saved_state
from .test_stashes import poll, progress, stash_game


def skill_game(lua, item=28051401):
    game, engine = stash_game(lua, items=(item,), rewards_stat_levels=1)
    lua.execute("""
        engine.recalculations=0
        haru_skills={skills_levels={}, skills_stats={}, skills_increments={}}
        for _,skill in ipairs({'strength','endurance','survival','scavenging'}) do
            haru_skills.skills_levels[skill]={current_level=0,max_level=15,
                base_requirement=750,requirement=750,experience=20}
            haru_skills.skills_stats[skill]={effect=1,functor='native'}
            haru_skills.skills_increments[skill]={effect=0.1}
            haru_skills['update_'..skill]=function()
                if engine.fail_recalculate then error('effect failed') end
                engine.recalculations=engine.recalculations+1
            end
        end
    """)
    return game, engine


@pytest.mark.parametrize("item", range(28051401, 28051405))
def test_skill_reward_updates_native_levels_stats_and_requirements_without_double_grants(lua, item):
    game, engine = skill_game(lua, item)
    engine.fail_recalculate = True
    poll(game, engine)
    skill = lua.globals().gamma_ap_catalog.skill_rewards[item]
    api = lua.globals().haru_skills
    assert api.skills_levels[skill].current_level == 1
    assert api.skills_levels[skill].requirement == 1687.5
    assert api.skills_levels[skill].experience == 750
    assert api.skills_stats[skill].effect == pytest.approx(1.1)
    game.load_state(saved_state(lua, game))
    engine.fail_recalculate = False
    poll(game, engine)
    assert progress(lua, game).received_count == 1
    assert api.skills_levels[skill].current_level == 1
    assert api.skills_stats[skill].effect == pytest.approx(1.1)


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_level", 16),
        ("current_level", -1),
        ("current_level", 0.5),
        ("current_level", 16),
        ("base_requirement", 0),
        ("experience", float("nan")),
    ],
)
def test_incompatible_skill_schema_refuses_receipt(lua, field, value):
    game, engine = skill_game(lua)
    lua.globals().haru_skills.skills_levels.strength[field] = value
    poll(game, engine)
    assert progress(lua, game).received_count == 0


def test_missing_skill_api_and_stat_increment_fail_before_level_mutation(lua):
    game, engine = skill_game(lua)
    api = lua.globals().haru_skills
    lua.globals().haru_skills = None
    poll(game, engine)
    lua.globals().haru_skills = api
    api.update_strength = None
    poll(game, engine)
    api.update_strength = lua.eval("function() end")
    api.skills_increments.strength.effect = None
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    assert api.skills_levels.strength.current_level == 0


def test_skill_cap_is_successful_without_adding_another_level(lua):
    game, engine = skill_game(lua)
    lua.globals().haru_skills.skills_levels.strength.current_level = 15
    poll(game, engine)
    assert progress(lua, game).received_count == 1
    assert lua.globals().haru_skills.skills_levels.strength.current_level == 15
    state = lua.globals().gamma_ap_state.new_state()
    assert lua.globals().gamma_ap_skills.receive(state, 28051401)[0] is False
