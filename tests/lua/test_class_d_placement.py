"""Expert Tools model Class D access without vetoing observed firearm use."""

import pytest

from .test_equipment_classes import fresh, native
from .test_tracker import rows


def class_d_state(lua, **options):
    state = fresh(
        lua,
        **(
            {
                "checks_weapon_tiers": 1,
                "rewards_progressive_tools": 1,
                "progressive_tool_receipts": 1,
                "tool_use_permissions": 1,
                "initial_firearm_class": 4,
                "regional_progression": 1,
                "playability_logic": 1,
                "rewards_faction_reputation": 1,
            }
            | options
        ),
    )
    # Satisfy the independent late-gear goodwill route, without any tool receipts.
    state.applied_items = lua.table_from([28051301] * 8)
    return state


@pytest.mark.parametrize("tier", [0, 1, 2, 3])
def test_class_d_pda_logic_requires_expert_tools(lua, tier):
    state = class_d_state(lua)
    state.applied_items = lua.table_from([28051301] * 8 + [28051801] * tier)
    row = lua.globals().gamma_ap_catalog.tracker_checks[28052754]
    reason = lua.globals().gamma_ap_progression_readiness.reason(state, row, lua.table(), 28052754)
    if tier == 3:
        assert reason is None
    else:
        assert reason is not None
        assert "AP placement logic" in reason and "Expert tools required" in reason
        assert "firearm use still counts" in reason


@pytest.mark.parametrize("playability", [0, 1])
def test_actual_class_d_use_counts_without_tools_and_retains_condition_and_prior_checks(
    lua, playability
):
    state = class_d_state(lua, playability_logic=playability)
    native(lua)
    lua.globals().metadata.rifle_d = lua.table(kind="w_rifle", repair_type="rifle_7")
    lua.execute("""
        weapon={health=.649,section=function() return 'rifle_d' end,
            condition=function(self) return self.health end}
        db={actor={item_in_slot=function() return nil end,
            active_item=function() return weapon end}}
    """)
    module = lua.globals().gamma_ap_equipment_checks
    assert module.poll(state, state.configuration)
    assert not state.checks[28052754]
    lua.globals().weapon.health = 0.65
    assert module.poll(state, state.configuration)
    assert state.checks[28052754]
    assert lua.globals().gamma_ap_workshop.tools_level(state) == 0
    snapshot = lua.globals().gamma_ap_tracker.snapshot(state, 0, None, False)
    assert next(row for row in rows(snapshot) if row.id == 28052754).status == "completed"
    lua.globals().weapon.health = 0.1
    assert module.poll(state, state.configuration) and state.checks[28052754]
