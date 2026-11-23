import json
from pathlib import Path

import pytest

from .test_workshop import poll, state_of, tool_game

ROWS = json.loads((Path(__file__).parents[2] / "src/gamma_archipelago/catalog.json").read_text())[
    "items"
]
REWARDS = [row for row in ROWS if row.get("filler_family")]


@pytest.mark.parametrize("row", REWARDS, ids=lambda row: row["name"])
def test_named_supply_filler_delivers_once_and_ammo_ignores_generic_package_calibre(lua, row):
    game, engine, _ = tool_game(
        lua,
        (row["id"],),
        rewards_progressive_tools=0,
        varied_filler=1,
        supply_ammo_calibre=4,
        **{row["category"]: 1},
    )
    poll(game, engine)
    assert state_of(lua, game).received_count == 1
    assert list(engine.created.values()) == row["supplies"]
    game.load_state(lua.table(gamma_archipelago_v1=state_of(lua, game)))
    poll(game, engine)
    assert list(engine.created.values()) == row["supplies"]


@pytest.mark.parametrize("enabled,category", [(0, 1), (1, 0)])
def test_disabled_filler_mode_or_category_never_applies_new_rewards(lua, enabled, category):
    game, engine, _ = tool_game(
        lua,
        (28051920,),
        rewards_progressive_tools=0,
        varied_filler=enabled,
        rewards_supply_medical=category,
    )
    poll(game, engine)
    assert state_of(lua, game).received_count == 0 and not list(engine.created)
