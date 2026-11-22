from gamma_archipelago.catalog import ITEM_SECTIONS, enabled_location_ids
from gamma_archipelago.configuration import encode_configuration

from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, KEY, configured_game


def collection_game(lua):
    # Keep coverage of all named source IDs and aliases alongside generic-mode tests.
    game, engine, configuration = configured_game(
        lua, checks_maps=0, checks_artefacts=1, artefact_discovery_mode=0
    )
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    game.actor_on_update()
    return game, engine, configuration


def artefact(lua, section):
    return lua.eval("function(section) return {section=function() return section end} end")(section)


def progress(lua, game):
    return saved_state(lua, game).gamma_archipelago_v1


def test_every_spawned_type_and_container_alias_counts_only_once(lua):
    game, _, configuration = collection_game(lua)
    aliases = lua.globals().gamma_ap_catalog.artefact_locations
    for section in aliases:
        item = artefact(lua, section)
        game.actor_on_item_take(item)
        game.actor_on_item_take_from_box(None, item)
        game.actor_on_item_take(item)  # Drop/pickup and a different condition cannot farm.
    state = progress(lua, game)
    expected = enabled_location_ids(configuration.checks)
    assert len(expected) == 66
    assert set(state.checks.keys()) == expected
    assert set(state.artefact_sources.keys()) == expected
    assert set(state.artefact_sources.values()) == {"ownership"}
    game.load_state(lua.table(gamma_archipelago_v1=state))
    game.actor_on_item_take(artefact(lua, next(iter(aliases))))
    assert set(progress(lua, game).checks.keys()) == expected


def test_box_source_is_preserved_across_save_copy(lua):
    game, _, _ = collection_game(lua)
    aliases = lua.globals().gamma_ap_catalog.artefact_locations
    section = next(iter(aliases))
    game.actor_on_item_take_from_box(None, artefact(lua, section))
    state = progress(lua, game)
    assert state.artefact_sources[aliases[section]] == "container"
    game.actor_on_item_take(artefact(lua, section))
    assert progress(lua, game).artefact_sources[aliases[section]] == "container"
    state.artefact_sources[aliases[section]] = "edited_copy"
    assert progress(lua, game).artefact_sources[aliases[section]] == "container"


def test_disabled_legacy_unbound_invalid_source_and_nonartefacts_do_not_count(lua):
    game, engine, _ = collection_game(lua)
    item = artefact(lua, "af_medusa")
    module = lua.globals().gamma_ap_collection
    state = lua.globals().gamma_ap_state.new_state()
    module.observe(state, item, "ownership")
    state.session_key = KEY
    module.observe(state, item, "ownership")
    state.expanded = True
    module.observe(state, item, "ownership")
    state.enabled_checks[lua.globals().gamma_ap_catalog.artefact_locations.af_medusa] = True
    module.observe(state, item, "archipelago")
    module.observe(state, None, "ownership")
    module.observe(state, artefact(lua, "af_unknown"), "ownership")
    for section in ITEM_SECTIONS.values():
        module.observe(state, artefact(lua, section), "ownership")
    assert not list(state.checks.keys())
    engine.alive = False
    game.actor_on_item_take(item)
    lua.globals().db.actor = None
    game.actor_on_item_take(item)
    assert not list(progress(lua, game).checks.keys())


def test_receipt_creation_callbacks_cannot_create_acquisition_feedback(lua):
    game, engine, _ = collection_game(lua)
    lua.globals().ap_game = game
    lua.execute("""
        alife_create_item=function(section,actor)
            ap_game.actor_on_item_take({section=function() return 'af_medusa' end})
            return {id=1}
        end
    """)
    # Reload the pre-receipt save so the next poll actually runs the grant.
    state = progress(lua, game)
    state.received_count = 0
    state.applied_items = lua.table()
    game.load_state(lua.table(gamma_archipelago_v1=state))
    engine.now += 1000
    game.actor_on_update()
    assert not list(progress(lua, game).checks.keys())
    game.actor_on_item_take(artefact(lua, "af_medusa"))
    assert progress(lua, game).checks[lua.globals().gamma_ap_catalog.artefact_locations.af_medusa]


def test_failed_reward_exception_clears_transient_acquisition_guard(lua):
    game, engine, _ = collection_game(lua)
    state = progress(lua, game)
    state.received_count = 0
    state.applied_items = lua.table()
    game.load_state(lua.table(gamma_archipelago_v1=state))
    lua.execute("alife_create_item=function() error('creation failed') end")
    engine.now += 1000
    game.actor_on_update()
    assert progress(lua, game).received_count == 0
    game.actor_on_item_take(artefact(lua, "af_medusa"))
    assert progress(lua, game).checks[lua.globals().gamma_ap_catalog.artefact_locations.af_medusa]
