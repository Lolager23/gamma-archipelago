from itertools import combinations

import pytest

from gamma_archipelago.activity_requirements import regional_requirement
from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.mutant_diversity import capacity
from gamma_archipelago.protocol import encode_incoming
from gamma_archipelago.web_planner import catalogue

from .test_loadout import KEY
from .test_tool_permissions import kit_game
from .test_tracker import state_for
from .test_workshop import INCOMING, poll, state_of


def fresh(lua, **values):
    return state_for(
        lua,
        **(
            {
                "regional_progression": 1,
                "equipment_class_progression": 1,
                "progressive_tool_receipts": 1,
                "rewards_starting_gear_unlocks": 1,
                "rewards_progressive_tools": 1,
                "rewards_recipe_access": 1,
            }
            | values
        ),
    )


def test_native_matching_agrees_with_core_for_reassignment_and_every_region_subset(lua):
    sources = (("a", "b"), ("a",), ("b",), ("c",), ("a", "b", "c")) * 3
    native = lua.globals().gamma_ap_mutant_diversity
    table = lua.table_from([lua.table_from(row) for row in sources])
    for count in range(4):
        for subset in combinations(("a", "b", "c"), count):
            regions = frozenset(subset)
            assert native.capacity(
                table, lua.table_from(dict.fromkeys(regions, True)), "a"
            ) == capacity(sources, regions, "a")
    assert native.capacity(lua.table(), lua.table(), "a") == 0


@pytest.mark.parametrize(
    "regions",
    [
        set(),
        {"l01_escape"},
        {"l01_escape", "l02_garbage"},
        {"l01_escape", "l02_garbage", "l03_agroprom"},
    ],
)
def test_mutant_quota_tracker_and_ap_projection_share_the_same_capacity(lua, regions):
    state = fresh(lua)
    config = build_configuration(defaults())
    native = lua.globals().gamma_ap_activity
    for row in catalogue()["locations"]:
        if row.get("quota_group") != "mutant":
            continue
        actual = native.available(
            state,
            lua.globals().gamma_ap_catalog.tracker_checks[row["id"]],
            lua.table_from(dict.fromkeys(regions, True)),
            row["id"],
        )
        expected = regional_requirement(row, config)
        assert actual == (expected.accessible(regions.__contains__), expected.reliable)


def test_story_readiness_explains_each_class_and_tool_gate(lua):
    state = fresh(lua)
    module = lua.globals().gamma_ap_progression_readiness
    row = lua.globals().gamma_ap_catalog.tracker_checks[28052607]
    regions = lua.table()
    assert "Class C" in module.reason(state, row, regions, 28052607)
    for i in (1, 2):
        state.applied_items[i] = 28053001
    assert "Medium" in module.reason(state, row, regions, 28052607)
    for i in (3, 4):
        state.applied_items[i] = 28053002
    assert "Advanced" in module.reason(state, row, regions, 28052607)
    for i in (5, 6):
        state.applied_items[i] = 28051801
    assert module.reason(state, row, regions, 28052607) is None
    path = lua.globals().gamma_ap_catalog.tracker_checks[28052611]
    assert "Class D" in module.reason(state, path, regions, 28052611)
    state.applied_items[7] = 28053001
    assert "Heavy" in module.reason(state, path, regions, 28052611)
    state.applied_items[8] = 28053002
    assert "Expert" in module.reason(state, path, regions, 28052611)
    state.applied_items[9] = 28051801
    assert module.reason(state, path, regions, 28052611) is None
    state.configuration.options.regional_progression = 0
    assert module.reason(state, row, regions, 28052607) is None


def test_northern_check_requires_real_shutdown_red_forest_and_another_northern_route(lua):
    state = fresh(lua)
    module = lua.globals().gamma_ap_progression_readiness
    row = lua.globals().gamma_ap_catalog.tracker_checks[28052716]
    regions = lua.table(l10_red_forest=True)
    assert module.reason(state, row, regions, 28052716)
    lua.execute("has_alife_info=function() return true end")
    assert module.reason(state, row, regions, 28052716)
    regions.l10_limansk = True
    assert module.reason(state, row, regions, 28052716) is None
    regions.l10_red_forest = False
    assert module.reason(state, row, regions, 28052716)


def test_artefact_recipe_reason_is_separate_from_the_melter(lua):
    state = fresh(lua)
    module = lua.globals().gamma_ap_progression_readiness
    row = lua.table(quota="artefact", minimum=21)
    assert "Recipe Access" in module.reason(state, row, lua.table(), 28140221)
    state.unlocks.recipe_artefact = True
    assert module.reason(state, row, lua.table(), 28140221) is None
    state.unlocks.recipe_artefact = False
    state.configuration.options.rewards_recipe_access = 0
    assert module.reason(state, row, lua.table(), 28140221) is None


def test_artefact_receipts_repeat_safely_and_request_full_condition_without_optional_supplies(lua):
    game, engine, config = kit_game(
        lua, (28053102, 28053102), rewards_artefacts=1, checks_artefacts=1, permission_supplies=0
    )
    # The first receipt has already applied through the real coordinator fixture.
    state = state_of(lua, game)
    assert state.received_count == 1
    lua.globals().adapter = game
    lua.execute("""
        local original=alife_create_item
        alife_create_item=function(section,actor,properties)
            engine.condition=properties and properties.cond
            local object=original(section,actor,properties)
            if object then
                local id=object.id
                object.id=function() return id end
                object.section=function() return section end
                adapter.actor_on_item_take(object)
            end
            return object
        end
    """)
    poll(game, engine)
    state = state_of(lua, game)
    assert state.received_count == 2 and engine.condition == 1
    assert list(engine.created.values()) == ["af_baloon_lead_box"] * 2
    game.load_state(lua.table(gamma_archipelago_v1=state))
    poll(game, engine)
    assert len(list(engine.created)) == 2 and not state_of(lua, game).refused_save
    assert not any(state.checks[id_] for id_ in range(28140201, 28140267))


def test_failed_artefact_delivery_retains_receipt_for_retry(lua):
    game, engine, config = kit_game(lua, rewards_artefacts=1, permission_supplies=0)
    engine.fail_reward = True
    engine.files[INCOMING] = encode_incoming(KEY, (28053101,), config.digest)
    poll(game, engine)
    state = state_of(lua, game)
    assert state.received_count == 0 and state.deliveries[1].next_action == 1
    assert "artefact pending" in lua.globals().gamma_ap_deliveries.summary(state)
    engine.fail_reward = False
    poll(game, engine)
    assert state_of(lua, game).received_count == 1
