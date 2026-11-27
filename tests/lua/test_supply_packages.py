import pytest

from .test_workshop import poll, state_of, tool_game


@pytest.mark.parametrize(
    "identity,category,expected",
    [
        (
            28051901,
            "medical",
            [
                "medkit_army",
                "medkit_army",
                "medkit_scientic",
                "bandage",
                "bandage",
                "antirad",
                "morphine",
                "drug_antidot",
            ],
        ),
        (
            28051902,
            "maintenance",
            [
                "gun_oil",
                "gun_oil",
                "solvent",
                "solvent",
                "glue_a",
                "glue_a",
                "sewing_kit_h",
                "duct_tape",
            ],
        ),
        (28051904, "expedition", ["bread", "water_drink", "bandage"]),
    ],
)
def test_package_receipts_repeat_deliberately_and_resume_after_save(
    lua, identity, category, expected
):
    game, engine, _ = tool_game(
        lua, (identity, identity), rewards_progressive_tools=0, **{f"rewards_supply_{category}": 1}
    )
    assert state_of(lua, game).received_count == 0 and len(list(engine.created.values())) == 1
    assert "package pending" in game.tracker_view().delivery
    saved = state_of(lua, game)
    game.load_state(lua.table(gamma_archipelago_v1=saved))
    for _ in range(len(expected) * 2 - 1):
        poll(game, engine)
    assert state_of(lua, game).received_count == 2
    assert list(engine.created.values()) == expected * 2
    assert lua.globals().gamma_ap_deliveries.validate(state_of(lua, game))
    assert not state_of(lua, game).unlocks.workshop_repair


@pytest.mark.parametrize(
    "calibre,section",
    list(
        enumerate(
            [
                "ammo_9x18_fmj",
                "ammo_9x19_fmj",
                "ammo_5.45x39_fmj",
                "ammo_5.56x45_ss190",
                "ammo_7.62x39_fmj",
            ]
        )
    ),
)
def test_ammunition_packages_use_seed_calibre_and_native_box_sizes(lua, calibre, section):
    game, engine, _ = tool_game(
        lua,
        (28051903,),
        rewards_progressive_tools=0,
        rewards_supply_ammunition=1,
        supply_ammo_calibre=calibre,
    )
    poll(game, engine)
    poll(game, engine)
    assert list(engine.created.values()) == [section] * 3
    assert state_of(lua, game).received_count == 1
