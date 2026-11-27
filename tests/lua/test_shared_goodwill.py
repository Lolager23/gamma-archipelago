import pytest

from .test_game_adapter import saved_state
from .test_stashes import poll, progress, stash_game

SHARED = 28051309
FACTIONS = ("stalker", "csky", "dolg", "freedom", "ecolog", "killer", "army", "bandit")


def setup(lua, **options):
    game, engine = stash_game(lua, items=(SHARED, SHARED), rewards_faction_reputation=1, **options)
    lua.execute("""
        engine.goodwill={};engine.sets={}
        relation_registry={community_goodwill=function(faction)
            if engine.bad_faction==faction then error('query') end
            return engine.goodwill[faction] or 0 end,
            set_community_goodwill=function(faction,id,target)
                engine.sets[faction]=(engine.sets[faction] or 0)+1
                if not engine.ignore_set then engine.goodwill[faction]=target end
                if engine.fail_faction==faction then error('after mutation') end
            end}
    """)
    return game, engine


def test_all_factions_receive_exact_bonus_and_partial_failure_retries_without_compounding(lua):
    game, engine = setup(lua)
    engine.fail_faction = "dolg"
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    assert engine.goodwill.stalker == 250 and engine.goodwill.dolg == 250
    saved = saved_state(lua, game)
    # A saved plan must be detached from the live plan.
    saved.gamma_archipelago_v1.reputation_targets[1].army = 999
    assert progress(lua, game).reputation_targets[1].army == 250
    game.load_state(saved_state(lua, game))
    engine.fail_faction = None
    poll(game, engine)
    assert progress(lua, game).received_count == 1
    assert all(engine.goodwill[faction] == 250 for faction in FACTIONS)
    poll(game, engine)
    assert progress(lua, game).received_count == 2
    assert all(engine.goodwill[faction] == 500 for faction in FACTIONS)


def test_shared_cap_floor_and_higher_natural_standing_are_preserved(lua):
    game, engine = setup(lua)
    engine.goodwill.stalker, engine.goodwill.dolg = 4000, 2990
    poll(game, engine)
    assert engine.goodwill.stalker == 4000 and engine.goodwill.dolg == 3000
    state = progress(lua, game)
    engine.goodwill.army = -2000
    assert lua.globals().gamma_ap_reputation.reconcile(state) is True
    assert engine.goodwill.army == 250
    state.applied_items = lua.table_from([SHARED] * 4 + [28051307])
    assert lua.globals().gamma_ap_settlement_access.reason(state, 28052103) is None
    floors = lua.globals().gamma_ap_settlement_access.minimum_goodwill(state)
    assert floors.army == 1250 and floors.dolg == 1000


def test_query_failure_plans_nothing_and_disabled_mode_refuses_new_id(lua):
    game, engine = setup(lua)
    engine.bad_faction = "bandit"
    poll(game, engine)
    assert not list(engine.sets.values())
    assert progress(lua, game).reputation_targets[1] is None
    engine.bad_faction = None
    game, engine = setup(lua, shared_faction_goodwill=0)
    poll(game, engine)
    assert progress(lua, game).received_count == 0


@pytest.mark.parametrize("target", ["bad", True, 0.5, 2147483648, {}, {"army": 250}])
def test_malformed_saved_targets_are_refused(lua, target):
    game, engine = setup(lua)
    poll(game, engine)
    state = progress(lua, game)
    state.reputation_targets[1] = lua.table_from(target) if isinstance(target, dict) else target
    assert lua.globals().gamma_ap_reputation.validate_targets(state) is False


def test_legacy_numeric_targets_still_load_and_shared_targets_need_the_matching_mode(lua):
    game, engine = setup(lua)
    poll(game, engine)
    state = progress(lua, game)
    module = lua.globals().gamma_ap_reputation
    state.reputation_targets = None
    assert module.validate_targets(state) is True
    state.reputation_targets = lua.table_from({1: 250})
    assert module.validate_targets(state) is True
    state.reputation_targets[1] = lua.table_from(dict.fromkeys(FACTIONS, 250))
    assert module.validate_targets(state) is True
    state.configuration.options.shared_faction_goodwill = 0
    assert module.validate_targets(state) is False
    state.reputation_targets = "bad"
    assert module.validate_targets(state) is False
