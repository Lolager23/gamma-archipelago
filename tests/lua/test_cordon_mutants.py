from .test_combat import combat_game, state_of, victim
from .test_tracker import state_for


def test_native_capacity_uses_the_shared_cordon_override(lua):
    module = lua.globals().gamma_ap_mutant_diversity
    sources = lua.table_from([lua.table_from(["l01_escape", "k01_darkscape"])] * 10)
    assert module.capacity(sources, lua.table(l01_escape=True), "l01_escape") == 3
    assert (
        module.capacity(sources, lua.table(l01_escape=True, k01_darkscape=True), "l01_escape") == 5
    )
    assert module.capacity(sources, lua.table(k01_darkscape=True), "k01_darkscape") == 5
    assert module.capacity(sources, lua.table(l01_escape=True), "k01_darkscape") == 2


def test_pda_marks_only_three_cordon_mutants_available(lua):
    state = state_for(lua, regional_progression=1, mutant_discovery_mode=1)
    catalogue = lua.globals().gamma_ap_catalog
    module = lua.globals().gamma_ap_activity
    for minimum in range(1, 6):
        identity = 28140000 + minimum
        row = catalogue.tracker_checks[identity]
        assert bool(module.available(state, row, lua.table(l01_escape=True), identity)[0]) == (
            minimum <= 3
        )
        assert module.available(
            state, row, lua.table(l01_escape=True, k01_darkscape=True), identity
        )[0]


def test_a_bonus_fourth_mutant_in_cordon_still_earns_actual_credit(lua):
    game, engine, _ = combat_game(lua, checks_mutant_first_kills=1, mutant_discovery_mode=1)
    actor = lua.globals().db.actor
    for index, section in enumerate(("boar", "flesh", "dog", "bloodsucker"), 1):
        native_class = next(
            key
            for key, name in lua.globals().gamma_ap_catalog.mutant_classes.items()
            if name == section
        )
        engine.meta[section] = lua.table()
        engine.meta[section]["class"] = native_class
        game.monster_on_death_callback(victim(lua, index, section), actor)
    state = state_of(lua, game)
    assert state.checks[28140004]
    assert state.discoveries[28052201]
