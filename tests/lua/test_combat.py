import pytest

from gamma_archipelago.catalog import KILL_MILESTONE_BASE, enabled_location_ids
from gamma_archipelago.configuration import encode_configuration
from gamma_archipelago.protocol import decode_outgoing, encode_confirmed

from .assertions import assert_lua_error
from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, KEY, configured_game


def combat_game(lua, **options):
    game, engine, configuration = configured_game(
        lua, checks_maps=0, checks_kill_milestones=1, kill_milestones=[1, 2, 4], **options
    )
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    lua.execute("db.actor.id=function() return 0 end")
    game.actor_on_update()
    return game, engine, configuration


def victim(lua, id_=1, section="dog", community="stalker", alive=False):
    factory = lua.eval("""function(id,section,community,live)
        return {id=function() return id end, name=function() return section..tostring(id) end,
            section=function() return section end,
            character_community=function() return community end,
            alive=function() return live end}
        end""")
    return factory(id_, section, community, alive)


def state_of(lua, game):
    return saved_state(lua, game).gamma_archipelago_v1


def test_actor_kills_deduplicate_hit_death_callbacks_and_survive_reload(lua):
    game, engine, configuration = combat_game(lua, checks_mutant_first_kills=1)
    engine.meta.dog = lua.table(class_="unused")
    engine.meta.dog["class"] = "SM_DOG_S"
    actor = lua.globals().db.actor
    dog = victim(lua)
    game.monster_on_hit_callback(dog, 1, None, actor, "head")
    game.monster_on_hit_callback(dog, 1, None, actor, "from_death_callback")
    game.monster_on_death_callback(dog, actor)
    state = state_of(lua, game)
    assert state.combat.kills == 1
    assert state.checks[KILL_MILESTONE_BASE + 1] is True
    assert state.checks[lua.globals().gamma_ap_catalog.mutant_locations.dog] is True
    game.load_state(lua.table(gamma_archipelago_v1=state))
    game.monster_on_death_callback(dog, actor)
    assert state_of(lua, game).combat.kills == 1
    game.monster_on_death_callback(victim(lua, 2), actor)
    assert state_of(lua, game).combat.kills == 2
    assert state.combat.kills == 1  # Saved copy is not mutated.
    engine.now += 1000
    game.actor_on_update()
    packet = engine.files["D:/AnomalyAP/appdata/archipelago\\outgoing.txt"]
    allowed = enabled_location_ids(configuration.checks, configuration.kill_milestones)
    assert decode_outgoing(packet, KEY, allowed).checked_locations <= allowed
    confirmations = encode_confirmed(KEY, frozenset({KILL_MILESTONE_BASE + 4}))
    parser = lua.globals().gamma_ap_protocol.parse_confirmed
    assert parser(confirmations, KEY)[KILL_MILESTONE_BASE + 4]
    assert_lua_error(parser(confirmations, KEY, lua.table()))


def test_every_species_kind_class_and_section_variant_has_a_first_kill_check(lua):
    game, engine, _ = combat_game(lua, checks_mutant_first_kills=1)
    actor = lua.globals().db.actor
    catalogue = lua.globals().gamma_ap_catalog
    for index, (class_, name) in enumerate(catalogue.mutant_classes.items(), 1):
        section = "test_" + name
        engine.meta[section] = lua.table()
        engine.meta[section]["class"] = class_
        game.monster_on_death_callback(victim(lua, index, section), actor)
        engine.meta[section].kind = class_
        engine.meta[section]["class"] = "UNKNOWN"
        game.monster_on_death_callback(victim(lua, index + 100, section), actor)
    for index, (prefix, _) in enumerate(catalogue.mutant_sections.items(), 200):
        for section in (prefix, prefix + "_strong"):
            game.monster_on_death_callback(victim(lua, index, section), actor)
    state = state_of(lua, game)
    assert all(state.checks[id_] is True for id_ in catalogue.mutant_locations.values())
    assert state.combat.kills == 4
    assert len(list(state.combat.seen.keys())) == 4  # Saturation bounds the history.


def test_factions_are_separate_and_story_aliases_are_canonical(lua):
    game, _, _ = combat_game(lua, checks_faction_first_kills=1)
    actor = lua.globals().db.actor
    for index, (name, id_) in enumerate(
        lua.globals().gamma_ap_catalog.faction_locations.items(), 1
    ):
        game.npc_on_death_callback(victim(lua, index, community=name), actor)
        assert state_of(lua, game).checks[id_] is True
    for name in ("army_npc", "greh_npc", "trader"):
        game.npc_on_death_callback(victim(lua, 99, community=name), actor)
    assert not any(
        state_of(lua, game).checks[id_]
        for id_ in lua.globals().gamma_ap_catalog.mutant_locations.values()
    )


@pytest.mark.parametrize("class_", ["SM_DOG_F", "AI_PHANT", "AI_CROW"])
def test_hallucinations_and_birds_do_not_count_as_mobs(lua, class_):
    game, engine, _ = combat_game(lua, checks_mutant_first_kills=1)
    engine.meta.dog = lua.table()
    engine.meta.dog["class"] = class_
    game.monster_on_death_callback(victim(lua), lua.globals().db.actor)
    assert state_of(lua, game).combat.kills == 0


def test_missing_nonactor_alive_self_and_unbound_deaths_are_ignored(lua):
    game, engine, _ = combat_game(lua)
    actor = lua.globals().db.actor
    for dead, killer in (
        (None, actor),
        (victim(lua), None),
        (victim(lua), victim(lua, 9)),
        (victim(lua, alive=True), actor),
        (victim(lua, 0), actor),
    ):
        game.npc_on_death_callback(dead, killer)
    engine.alive = False
    game.npc_on_death_callback(victim(lua), actor)
    engine.alive = True
    lua.globals().db.actor = None
    game.npc_on_death_callback(victim(lua), actor)
    lua.globals().db.actor = actor
    empty = lua.globals().gamma_ap_state.new_state()
    lua.globals().gamma_ap_combat.observe(empty, "faction", victim(lua), actor)
    empty.session_key = KEY
    lua.globals().gamma_ap_combat.observe(empty, "faction", victim(lua), actor)
    assert state_of(lua, game).combat.kills == 0


def test_id_reuse_is_reset_only_for_a_living_spawn_and_older_save_restores_count(lua):
    game, _, _ = combat_game(lua)
    actor = lua.globals().db.actor
    object_ = victim(lua)
    game.npc_on_death_callback(object_, actor)
    earlier = saved_state(lua, game)
    game.creature_spawned(None)
    game.creature_spawned(object_)
    game.npc_on_death_callback(object_, actor)
    assert state_of(lua, game).combat.kills == 1
    game.creature_spawned(victim(lua, alive=True))
    game.npc_on_death_callback(object_, actor)
    assert state_of(lua, game).combat.kills == 2
    game.load_state(earlier)
    assert state_of(lua, game).combat.kills == 1


def test_kill_counter_is_disabled_independently_of_first_species_checks(lua):
    game, engine, configuration = configured_game(lua, checks_mutant_first_kills=1)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    lua.execute("db.actor.id=function() return 0 end")
    game.actor_on_update()
    engine.meta.dog = lua.table()
    engine.meta.dog["class"] = "SM_DOG_S"
    game.monster_on_death_callback(victim(lua), lua.globals().db.actor)
    assert state_of(lua, game).combat.kills == 0
    assert state_of(lua, game).checks[lua.globals().gamma_ap_catalog.mutant_locations.dog]
