import pytest

from gamma_archipelago.configuration import encode_configuration

from .test_loadout import CONFIG_PATH, KEY, configured_game
from .test_workshop import state_of


@pytest.mark.parametrize("readiness", [1, 2])
def test_pda_combat_reasons_match_selected_ap_permission_assumptions(lua, readiness):
    game, engine, configuration = configured_game(
        lua,
        combat_logic=readiness,
        checks_mutant_first_kills=1,
        starting_firearms=2,
        starting_outfit=2,
        starting_helmet=2,
        rewards_starting_gear_unlocks=1,
    )
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    game.on_game_start()
    engine.creation.new_game_faction = None
    engine.objects = lua.table()
    game.actor_on_update()

    def rows():
        return [
            row
            for row in game.tracker_view().rows.values()
            if row.category == "checks_mutant_first_kills"
        ]

    assert rows() and all("firearms" in row.reason for row in rows())
    state = state_of(lua, game)
    state.unlocks.gear_firearms = True
    game.load_state(lua.table(gamma_archipelago_v1=state))
    if readiness == 2:
        assert all("outfit" in row.reason for row in rows())
        state.unlocks.gear_outfit = True
        game.load_state(lua.table(gamma_archipelago_v1=state))
        assert all("helmet" in row.reason for row in rows())
        state.unlocks.gear_helmet = True
        game.load_state(lua.table(gamma_archipelago_v1=state))
    assert all(row.status == "available" for row in rows())
