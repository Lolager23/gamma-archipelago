"""The PDA uses the same catalogue boundaries as the actual AP solver."""

import pytest

from .test_tracker import state_for


@pytest.mark.parametrize(
    "minimum,tools,outfit,firearms",
    [
        (10, 0, 1, 1),
        (11, 2, 3, 2),
        (15, 2, 3, 2),
        (16, 3, 4, 3),
        (25, 3, 4, 3),
    ],
)
def test_pda_mutant_readiness_matches_exact_gear_and_tool_boundaries(
    lua, minimum, tools, outfit, firearms
):
    state = state_for(
        lua,
        regional_progression=1,
        equipment_class_progression=1,
        rewards_starting_gear_unlocks=1,
        rewards_progressive_tools=1,
        progressive_tool_receipts=1,
        initial_firearm_class=firearms,
        initial_outfit_class=outfit,
    )
    state.applied_items = lua.table_from([28051801] * tools)
    row = lua.table(quota="mutant", minimum=minimum)
    reason = lua.globals().gamma_ap_progression_readiness.reason
    regions = lua.table()
    identity = 28140000 + minimum
    assert reason(state, row, regions, identity) is None
    if not tools:
        return
    state.applied_items = lua.table_from([28051801] * (tools - 1))
    assert ("Advanced" if tools == 2 else "Expert") in reason(state, row, regions, identity)
    state.applied_items = lua.table_from([28051801] * tools)
    for option in ("initial_firearm_class", "initial_outfit_class"):
        state.configuration.options[option] -= 1
        assert "Mutant discovery equipment required:" in reason(state, row, regions, identity)
        state.configuration.options[option] += 1
    state.configuration.options.regional_progression = 0
    state.applied_items = lua.table()
    assert reason(state, row, regions, identity) is None


def test_class_a_check_is_not_a_basic_tool_use_permission(lua):
    state = state_for(lua, rewards_progressive_tools=1, equipment_class_progression=1)
    reason = lua.globals().gamma_ap_tool_permissions.grade_reason
    assert reason(state, lua.table(category="checks_weapon_tiers", weapon_grade="A")) is None
    assert reason(state, lua.table(category="checks_weapon_tiers", weapon_grade="B"))
    state.unlocks.tool_basic = True
    assert reason(state, lua.table(category="checks_weapon_tiers", weapon_grade="B")) is None


def test_using_a_class_a_firearm_can_report_the_check_before_any_tool_receipt(lua):
    from .test_tool_permissions import kit_game
    from .test_workshop import poll, state_of

    game, engine, _ = kit_game(
        lua, checks_weapon_tiers=1, playability_logic=0, checks_gear_upgrades=0
    )
    lua.execute("""make_class_a=function()
        return {section=function() return 'test_pistol' end,condition=function() return 1 end}
    end""")
    engine.meta.test_pistol = lua.table(kind="w_pistol", repair_type="pistol")
    engine.active = lua.globals().make_class_a()
    poll(game, engine)
    state = state_of(lua, game)
    assert not state.unlocks.tool_basic
    assert state.checks[lua.globals().gamma_ap_catalog.weapon_grade_locations.pistol]
