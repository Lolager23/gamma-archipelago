import pytest

from .test_tracker import rows, state_for, view


def reason(lua, state, category, **fields):
    row = lua.table_from({"category": category, "minimum": 0, "quota": "", **fields})
    return lua.globals().gamma_ap_playability.reason(state, row, lua.table_from({}), False)


def test_knife_limits_and_legacy_mode_match_world_rules(lua):
    state = state_for(lua, starting_firearms=2, rewards_starting_gear_unlocks=1)
    assert reason(lua, state, "checks_mutant_first_kills", minimum=5, quota="mutant") is None
    assert "Firearms required" in reason(
        lua, state, "checks_mutant_first_kills", minimum=6, quota="mutant"
    )
    assert "Firearms required" in reason(lua, state, "checks_mutant_first_kills")
    assert reason(lua, state, "checks_kill_milestones", minimum=25) is None
    assert "Firearms required" in reason(lua, state, "checks_kill_milestones", minimum=26)
    assert "Firearms required" in reason(lua, state, "checks_faction_first_kills")
    state.unlocks.gear_firearms = True
    assert reason(lua, state, "checks_faction_first_kills") is None
    state.configuration.options.playability_logic = 0
    assert reason(lua, state, "checks_armour_tiers", key="4") is None


def test_goodwill_proxy_and_northern_alternative_use_ap_history(lua):
    state = state_for(lua, rewards_faction_reputation=1)
    state.applied_items = lua.table_from([28051301] * 7 + [28051305] * 7 + [28051001])
    assert "AP-granted faction goodwill" in reason(
        lua, state, "checks_rank_milestones", minimum=49999
    )
    assert reason(lua, state, "checks_faction_standing", minimum=1000) is None
    assert "Heavy equipment" in reason(lua, state, "checks_armour_tiers", key="3")
    module = lua.globals().gamma_ap_playability
    row = lua.table_from(dict(category="checks_armour_tiers", key="4"))
    assert (
        module.reason(state, row, lua.table_from(dict(l10_red_forest=True, jupiter=True)), True)
        is None
    )
    assert "Heavy equipment" in module.reason(state, row, lua.table_from(dict(jupiter=True)), True)
    state.applied_items[16] = 28051301
    assert reason(lua, state, "checks_armour_tiers", key="4") is None
    state.applied_items = lua.table_from([28051301] * 12)
    assert reason(lua, state, "checks_rank_milestones", minimum=49999) is None


def test_tracker_explains_capability_and_rank_blocks(lua):
    state = state_for(
        lua,
        checks_mutant_first_kills=1,
        checks_rank_milestones=1,
        rewards_faction_reputation=1,
        starting_firearms=2,
        rewards_starting_gear_unlocks=1,
    )
    projected = {row.id: row for row in rows(view(lua, state))}
    assert "AP-granted" in projected[28052802].reason


@pytest.mark.parametrize("policy", [0, 1, 2])
@pytest.mark.parametrize("enabled", [0, 1])
def test_paid_shop_manifest_is_independent_of_fragile_policy_only_in_new_logic(
    lua, policy, enabled
):
    state = state_for(
        lua, checks_shop_purchases=1, optional_check_policy=policy, playability_logic=enabled
    )
    actual = {id for id in state.enabled_checks if 28052921 <= id <= 28052929}
    assert len(actual) == (9 if enabled or policy != 1 else 0)
