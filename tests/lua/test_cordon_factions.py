from .test_combat import combat_game, state_of, victim
from .test_tracker import state_for


def test_pda_availability_uses_two_cordon_factions_and_military_requires_agroprom(lua):
    state = state_for(lua)
    catalogue = lua.globals().gamma_ap_catalog
    module = lua.globals().gamma_ap_activity
    cordon = lua.table(l01_escape=True)
    assert module.available(state, catalogue.tracker_checks[28140102], cordon, 28140102)[0]
    assert not module.available(state, catalogue.tracker_checks[28140103], cordon, 28140103)[0]
    assert not module.available(state, catalogue.tracker_checks[28052308], cordon, 28052308)[0]
    agroprom = lua.table(l03_agroprom=True)
    assert module.available(state, catalogue.tracker_checks[28052308], agroprom, 28052308)[0]


def test_a_bonus_military_kill_in_cordon_still_earns_the_actual_discovery(lua):
    game, engine, _ = combat_game(lua, checks_faction_first_kills=1, faction_discovery_mode=1)
    actor = lua.globals().db.actor
    for index, faction in enumerate(("stalker", "bandit", "army"), 1):
        game.npc_on_death_callback(victim(lua, index, community=faction), actor)
    state = state_of(lua, game)
    assert state.checks[28140103]
    assert state.discoveries[28052308]
