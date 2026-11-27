import pytest

from .test_workshop import poll, state_of, tool_game


@pytest.mark.parametrize(
    "identity,category,old",
    [
        (28051901, "medical", ["medkit", "bandage", "antirad"]),
        (28051902, "maintenance", ["gun_oil", "glue_a", "duct_tape"]),
    ],
)
def test_in_progress_legacy_plan_keeps_its_cursor_then_next_receipt_uses_new_contents(
    lua, identity, category, old
):
    game, engine, _ = tool_game(
        lua, (identity, identity), rewards_progressive_tools=0, **{f"rewards_supply_{category}": 1}
    )
    saved = state_of(lua, game)
    plan = saved.deliveries[1]
    plan.version = None
    plan.sections = lua.table_from(old)
    # Restore the old save's one already-created object alongside its AP cursor.
    engine.created[1] = old[0]
    game.load_state(lua.table(gamma_archipelago_v1=saved))
    assert lua.globals().gamma_ap_deliveries.validate(state_of(lua, game))
    for _ in range(10):
        poll(game, engine)
    current = state_of(lua, game)
    assert current.received_count == 2
    assert list(engine.created.values())[:3] == old
    assert current.deliveries[1].version is None
    assert current.deliveries[2].version == 2
    assert len(current.deliveries[2].sections) == 8
    assert len(engine.created) == 11
    game.load_state(lua.table(gamma_archipelago_v1=current))
    poll(game, engine)
    assert len(engine.created) == 11


@pytest.mark.parametrize("version", [0, 1, 3, "2", True])
def test_unknown_supply_plan_version_is_refused_before_mutation(lua, version):
    game, _, _ = tool_game(lua, (28051901,), rewards_progressive_tools=0, rewards_supply_medical=1)
    state = state_of(lua, game)
    state.deliveries[1].version = version
    assert lua.globals().gamma_ap_deliveries.validate(state) is False
