"""Worn helmets and outfits provide alternative routes to the same armour checks."""

import pytest

from .test_equipment_classes import fresh, native
from .test_tracker import rows, view


def helmet_state(lua, tier=3, **options):
    state = fresh(
        lua,
        **(
            {
                "checks_armour_tiers": 1,
                "playability_logic": 0,
                "initial_outfit_class": 0,
                "initial_helmet_class": tier,
            }
            | options
        ),
    )
    native(lua)
    lua.execute("""
        metadata.test_helmet={kind='o_helmet',class='E_HLMET'}
        worn={health=.65,section=function() return 'test_helmet' end,
            condition=function(self) return self.health end}
        db={actor={item_in_slot=function(self,slot) return slot==12 and worn or nil end}}
    """)
    lua.globals().metadata.test_helmet.repair_type = (
        "helmet_light",
        "helmet_medium",
        "helmet_heavy",
        "helmet_exo",
    )[tier - 1]
    return state


@pytest.mark.parametrize("tier", [1, 2, 3, 4])
def test_worn_helmet_credits_its_tier_and_skipped_lower_tiers_without_outfit_permission(lua, tier):
    state = helmet_state(lua, tier)
    module = lua.globals().gamma_ap_equipment_checks
    assert module.poll(state, state.configuration)
    for rank in range(1, 5):
        assert bool(state.checks[28052700 + rank]) == (rank <= tier)
    saved = lua.globals().gamma_ap_state.copy_state(state)
    lua.globals().worn = None
    assert module.poll(saved, saved.configuration)
    assert saved.checks[28052700 + tier]


@pytest.mark.parametrize(
    "rejection",
    ["below_condition", "broken", "locked", "carried", "unknown", "wrong_kind", "disabled"],
)
def test_helmet_requires_wearing_permission_condition_and_known_tier(lua, rejection):
    state = helmet_state(lua)
    if rejection == "below_condition":
        lua.globals().worn.health = 0.649
    elif rejection == "broken":
        lua.globals().worn.health = 0
    elif rejection == "locked":
        state.configuration.options.initial_helmet_class = 2
    elif rejection == "carried":
        lua.execute("db.actor.item_in_slot=function() return nil end")
    elif rejection == "unknown":
        state.configuration.options.initial_helmet_class = 4
        lua.globals().metadata.test_helmet.repair_type = "unknown"
    elif rejection == "wrong_kind":
        lua.globals().metadata.test_helmet.kind = "i_device"
        lua.globals().metadata.test_helmet["class"] = "D_CUSTOM"
    else:
        state.configuration.options.checks_armour_tiers = 0
    assert lua.globals().gamma_ap_equipment_checks.poll(state, state.configuration)
    assert not list(state.checks)


@pytest.mark.parametrize("classes", [0, 1])
def test_tracker_accepts_helmet_route_without_outfit_and_explains_either_permission(lua, classes):
    state = fresh(
        lua,
        checks_armour_tiers=1,
        equipment_class_progression=classes,
        starting_outfit=2,
        starting_helmet=2,
        initial_outfit_class=0,
        initial_helmet_class=0,
        playability_logic=0,
    )
    check = {row.id: row for row in rows(view(lua, state))}[28052703]
    assert (
        check.status == "blocked"
        and "outfit" in check.reason.lower()
        and "helmet" in check.reason.lower()
    )
    if classes:
        state.configuration.options.initial_helmet_class = 3
    else:
        state.unlocks.gear_helmet = True
    check = {row.id: row for row in rows(view(lua, state))}[28052703]
    assert check.status == "available"


def test_legacy_worn_helmet_does_not_require_generic_outfit_unlock(lua):
    state = helmet_state(lua, equipment_class_progression=0, starting_outfit=2, starting_helmet=2)
    state.unlocks.gear_helmet = True
    assert lua.globals().gamma_ap_equipment_checks.poll(state, state.configuration)
    assert state.checks[28052703] and not state.unlocks.gear_outfit
