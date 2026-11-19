import pytest

from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
from gamma_archipelago.discovery import GROUPS, QUOTAS, SOURCES, configured_location_ids

from .test_collection import artefact
from .test_combat import victim
from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, KEY, configured_game


def discovery_game(lua, **values):
    game, engine, configuration = configured_game(lua, **values)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    lua.execute("db.actor.id=function() return 0 end")
    game.actor_on_update()
    return game, engine, configuration


def progress(lua, game):
    return saved_state(lua, game).gamma_archipelago_v1


@pytest.mark.parametrize("group", GROUPS)
def test_distinct_quota_any_order_duplicates_disabled_totals_and_save_reload(lua, group):
    count = 15 if group == "mutant" else 3
    game, _, configuration = discovery_game(
        lua,
        **{
            GROUPS[group]: 1,
            f"{group}_discovery_mode": 1,
            f"{group}_discovery_count": count,
            "discovery_exclusions": [next(iter(SOURCES[group]))],
        },
    )
    module = lua.globals().gamma_ap_discovery
    state = progress(lua, game)
    assert set(state.enabled_checks) == configured_location_ids(configuration)
    excluded = next(iter(SOURCES[group].values()))
    assert not module.record(state, excluded)
    assert not module.record(state, 123)
    roster = list(SOURCES[group].values())[1:][::-1]
    for source in roster[: count - 1]:
        assert module.record(state, source)
        assert not module.record(state, source)
    assert set(state.checks) - {28052001} == set(QUOTAS[group][: count - 1])
    game.load_state(lua.table(gamma_archipelago_v1=state))
    loaded = progress(lua, game)
    assert set(loaded.discoveries) == set(roster[: count - 1])
    for source in roster:
        module.record(loaded, source)
    assert set(loaded.checks) - {28052001} == set(QUOTAS[group][:count])
    assert not list(state.combat.thresholds.values())
    loaded.discoveries[roster[0]] = None
    assert progress(lua, game).discoveries[roster[0]]


def test_native_mutant_and_artefact_callbacks_advance_quotas_not_source_checks(lua):
    game, engine, _ = discovery_game(
        lua,
        checks_mutant_first_kills=1,
        mutant_discovery_mode=1,
        mutant_discovery_count=1,
        checks_artefacts=1,
        artefact_discovery_mode=1,
        artefact_discovery_count=1,
    )
    actor = lua.globals().db.actor
    for section in ("dog", "dog_strong"):
        engine.meta[section] = lua.table()
        engine.meta[section]["class"] = "SM_DOG_S"
    game.monster_on_death_callback(victim(lua, section="dog"), actor)
    game.monster_on_death_callback(victim(lua, section="dog_strong"), actor)
    game.actor_on_item_take(artefact(lua, "af_medusa"))
    game.actor_on_item_take_from_box(None, artefact(lua, "af_medusa"))
    state = progress(lua, game)
    assert set(state.checks) - {28052001} == {QUOTAS["mutant"][0], QUOTAS["artefact"][0]}
    assert len(list(state.discoveries)) == 2 and state.combat.kills == 0


@pytest.mark.parametrize("change", [123, {123: True}, {28052201: False}])
def test_invalid_saved_discovery_state_is_refused(lua, change):
    game, _, _ = discovery_game(lua)
    state = progress(lua, game)
    state.discoveries = lua.table_from(change) if isinstance(change, dict) else change
    game.load_state(lua.table(gamma_archipelago_v1=state))
    assert progress(lua, game).refused_save


@pytest.mark.parametrize("excluded", [False, True])
def test_saved_discoveries_cannot_include_disabled_or_excluded_types(lua, excluded):
    token, source = next(iter(SOURCES["mutant"].items()))
    game, _, _ = discovery_game(
        lua,
        checks_mutant_first_kills=int(excluded),
        mutant_discovery_mode=1,
        mutant_discovery_count=2,
        discovery_exclusions=[token] if excluded else [],
    )
    state = progress(lua, game)
    state.discoveries[source] = True
    game.load_state(lua.table(gamma_archipelago_v1=state))
    assert progress(lua, game).refused_save


def test_saved_discovery_validation_requires_a_well_shaped_configuration(lua):
    module = lua.globals().gamma_ap_discovery
    seen = lua.table_from({next(iter(SOURCES["mutant"].values())): True})
    assert not module.validate(seen, KEY, None)
    assert not module.validate(seen, KEY, lua.table())
    assert not module.validate(seen, KEY, lua.table(options=lua.table(), exclusions=7))


def test_legacy_state_migration_disabled_types_and_session_validation(lua):
    game, _, _ = discovery_game(lua)
    state = progress(lua, game)
    state.discoveries = None
    game.load_state(lua.table(gamma_archipelago_v1=state))
    loaded = progress(lua, game)
    assert not list(loaded.discoveries)
    module = lua.globals().gamma_ap_discovery
    assert not module.record(loaded, 28052201)
    assert module.validate(None, None)
    assert not module.validate(lua.table_from({28052201: True}), None)
    legacy = lua.globals().gamma_ap_state.new_state()
    assert not module.record(legacy, 28052201)
    legacy.enabled_checks[28052201] = True
    assert module.record(legacy, 28052201)


def test_native_configuration_validates_exclusions_and_quota_bounds(lua):
    parser = lua.globals().gamma_ap_configuration.parse
    configuration = build_configuration(
        {
            **defaults(),
            "checks_mutant_first_kills": 1,
            "mutant_discovery_mode": 1,
            "mutant_discovery_count": 25,
        }
    )
    content = encode_configuration(KEY, configuration, expanded=True)
    for replacement in (
        "exclude|unknown",
        "exclude|mutant:dog\nexclude|mutant:dog",
        "exclude|mutant:dog",
    ):
        lines = content.splitlines()[:-1] + replacement.splitlines()
        broken = "\n".join(lines + [f"end|{len(lines) - 3}"]) + "\n"
        result, reason = parser(broken, KEY, configuration.digest)
        assert result is None and ("exclusion" in reason or "quota" in reason)


def test_quota_ids_are_not_side_task_previews_and_optional_policy_matches(lua):
    game, _, configuration = discovery_game(
        lua,
        checks_mutant_first_kills=1,
        mutant_discovery_mode=1,
        mutant_discovery_count=2,
        checks_shops=1,
        optional_check_policy=1,
        reward_previews=1,
    )
    state = progress(lua, game)
    assert set(state.enabled_checks) == configured_location_ids(configuration)
    assert not list(lua.globals().gamma_ap_scouting.previews(state).values())
    old = lua.globals().gamma_ap_configuration.copy(state.configuration)
    old.exclusions = None
    assert not list(lua.globals().gamma_ap_configuration.copy(old).exclusions)
