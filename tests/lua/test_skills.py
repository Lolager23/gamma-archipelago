import pytest

from gamma_archipelago.notifications import Notice, decode_acknowledgements, encode_notices
from gamma_archipelago.protocol import encode_incoming

from .test_game_adapter import enter_world, saved_state
from .test_loadout import KEY
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


@pytest.mark.parametrize("item", range(28051401, 28051404))
@pytest.mark.parametrize("natural_level", [1, 2])
def test_recalculation_retry_preserves_xp_and_levels_earned_since_first_attempt(
    lua, item, natural_level
):
    game, engine = skill_game(lua, item)
    engine.fail_recalculate = True
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    skill = lua.globals().gamma_ap_catalog.skill_rewards[item]
    api = lua.globals().haru_skills
    levels, stats = api.skills_levels[skill], api.skills_stats[skill]
    levels.experience = 1200
    if natural_level == 2:
        levels.current_level = 2
        levels.prev_requirement, levels.requirement = 1687.5, 2812.5
        levels.experience, stats.effect = 2000, 1.2
    expected_levels, expected_stats = dict(levels.items()), dict(stats.items())
    game.load_state(saved_state(lua, game))
    engine.fail_recalculate = False
    poll(game, engine)
    assert progress(lua, game).received_count == 1
    assert dict(levels.items()) == expected_levels
    assert dict(stats.items()) == expected_stats
    assert engine.recalculations == 1


@pytest.mark.parametrize("value", [None, float("nan"), 16])
def test_saved_skill_plan_does_not_bypass_native_schema_validation_on_retry(lua, value):
    game, engine = skill_game(lua)
    engine.fail_recalculate = True
    poll(game, engine)
    lua.globals().haru_skills.skills_levels.strength.current_level = value
    engine.fail_recalculate = False
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    assert "schema is incompatible" in list(engine.logs.values())[-1]


@pytest.mark.parametrize("item", range(28051401, 28051405))
@pytest.mark.parametrize("current", [0, 15, 29, 30])
def test_gamma_30_level_skills_apply_once_respect_cap_and_survive_recalculation_retry(
    lua, item, current
):
    game, engine = skill_game(lua, item)
    skill = lua.globals().gamma_ap_catalog.skill_rewards[item]
    api = lua.globals().haru_skills
    levels = api.skills_levels[skill]
    levels.max_level, levels.current_level = 30, current
    engine.fail_recalculate = skill != "scavenging"
    poll(game, engine)
    target = min(30, current + 1)
    assert levels.current_level == target
    assert api.skills_stats[skill].effect == pytest.approx(1 if current == 30 else 1.1)
    game.load_state(saved_state(lua, game))
    engine.fail_recalculate = False
    poll(game, engine)
    assert progress(lua, game).received_count == 1
    assert levels.current_level == target
    assert api.skills_stats[skill].effect == pytest.approx(1 if current == 30 else 1.1)
    poll(game, engine)
    assert progress(lua, game).received_count == 1


def test_gamma_skill_reward_unblocks_later_delivery_and_pda_notices_without_replaying(lua):
    game, engine = skill_game(lua, 28051403)
    lua.execute("""
        haru_skills.skills_levels.survival.max_level=30
        engine.news={}
        db.actor.give_game_news=function(self,title,text)
            engine.news[#engine.news+1]=text
        end
    """)
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = encode_incoming(
        KEY, (28051403, 28051003), engine.configuration_key
    )
    engine.files["D:/AnomalyAP/appdata/archipelago\\notices.txt"] = encode_notices(
        KEY, (Notice("r:0", 1, "Survival unlocked"), Notice("r:1", 2, "Bandage delivered"))
    )
    engine.fail_recalculate = True
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    assert not list(engine.news.values())
    assert not list(engine.spawns)
    game.load_state(saved_state(lua, game))
    enter_world(engine)
    engine.fail_recalculate = False
    for _ in range(3):
        poll(game, engine)
    assert progress(lua, game).received_count == 2
    assert lua.globals().haru_skills.skills_levels.survival.current_level == 1
    assert len(list(engine.spawns)) == 1
    assert list(engine.news.values()) == ["Survival unlocked", "Bandage delivered"]
    ack = engine.files["D:/AnomalyAP/appdata/archipelago\\notices_ack.txt"]
    assert decode_acknowledgements(ack, KEY) == {"r:0", "r:1"}
    game.load_state(saved_state(lua, game))
    enter_world(engine)
    poll(game, engine)
    assert len(list(engine.spawns)) == 1 and len(list(engine.news)) == 2


def test_gamma_survival_balance_accepts_negative_base_stats_and_saved_level_schema(lua):
    game, engine = skill_game(lua, 28051403)
    lua.execute("""
        haru_skills.skills_levels.survival={current_level=0,max_level=30,
            base_requirement=750,requirement=750,experience=209.3,prev_requirement=0}
        haru_skills.skills_stats.survival={resistance=1,bleed_restore=0,hunting_skill=-4,
            functor='haru_skills.update_survival'}
        haru_skills.skills_increments.survival={resistance=0,bleed_restore=.00005,hunting_skill=.25}
    """)
    poll(game, engine)
    api = lua.globals().haru_skills
    assert progress(lua, game).received_count == 1
    assert api.skills_levels.survival.current_level == 1
    assert api.skills_levels.survival.experience == 750
    assert api.skills_levels.survival.requirement == 1687.5
    assert api.skills_stats.survival.hunting_skill == -3.75
    assert api.skills_stats.survival.bleed_restore == pytest.approx(0.00005)
    assert api.skills_stats.survival.resistance == 1
