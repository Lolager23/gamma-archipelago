import pytest

from gamma_archipelago.configuration import encode_configuration
from gamma_archipelago.protocol import encode_incoming

from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, KEY, configured_game

FIRST = 28051101
ADVANCED = 28051127


def stash_game(lua, *, items=(FIRST,), **options):
    lua.globals().modxml_gamma_ap_stashes = lua.table(
        registered=True, ready=lua.eval("function() return true end")
    )
    game, engine, configuration = configured_game(lua, rewards_loot_stashes=1, **options)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = encode_incoming(
        KEY, items, configuration.digest
    )
    lua.execute("""
        engine.servers={}; engine.boxes={}; engine.markers={}; engine.spawns={}
        engine.serial=100; engine.spawn_calls=0
        db.actor.id=function() return 0 end
        ini_sys.section_exist=function(self,section) return engine.missing_section~=section end
        treasure_manager={caches={}}
        alife_object=function(id) return engine.servers[id] end
        alife=function() return {level_name=function(self,id) return id end} end
        game_graph=function() return {vertex=function(self,id)
            return {level_id=function() return id end}
        end} end
        IsInvbox=function(object,class) return class=='invbox' end
        level.object_by_id=function(id) return engine.boxes[id] end
        level.map_has_object_spot=function(id,kind)
            if engine.fail_marker then error('map API failed') end
            return engine.markers[id..':'..kind] and 1 or 0
        end
        level.map_add_object_spot_ser=function(id,kind,hint) engine.markers[id..':'..kind]=hint end
        level.map_change_spot_hint=function(id,kind,hint) engine.markers[id..':'..kind]=hint end
        level.map_remove_object_spot=function(id,kind) engine.markers[id..':'..kind]=nil end
        make_cache=function(id,name,where,parent,class)
            local server={id=id,parent_id=parent,m_game_vertex_id=where}
            server.name=function() return name end
            server.clsid=function() return class end
            local box={id=function() return id end,name=function() return name end}
            engine.servers[id]=server; engine.boxes[id]=box; treasure_manager.caches[id]=false
            return box
        end
        alife_create_item=function(section,owner)
            engine.spawn_calls=engine.spawn_calls+1
            if engine.raise_spawn then error('creation threw') end
            if engine.fail_spawn then return nil end
            engine.serial=engine.serial+1
            local id=engine.serial
            local name=section..tostring(id)
            engine.spawns[id]={section=section,owner=owner:id(),name=name}
            if engine.bad_identity then return {id='bad',name=function() return name end} end
            if engine.game_object_result then
                return {id=function() return id end,name=function() return name end}
            end
            return {id=id,name=function() return name end}
        end
    """)
    names = sorted(lua.globals().gamma_ap_catalog.stash_containers.keys())
    for id_, name in enumerate(names[:3], 1):
        lua.globals().make_cache(id_, name, "l01_escape", 65535, "invbox")
    return game, engine


def progress(lua, game):
    return saved_state(lua, game).gamma_archipelago_v1


def poll(game, engine):
    engine.now += 1000
    game.actor_on_update()


def test_receipt_reveals_fixed_coordinates_and_opens_a_saved_nonrerolling_package(lua):
    game, engine = stash_game(lua)
    poll(game, engine)
    state = progress(lua, game)
    record = state.stashes.records[1]
    assert state.received_count == 1 and not record.opened
    assert engine.spawn_calls == 0
    assert engine.markers[f"{record.cache_id}:gamma_ap_loot"]
    original_sections = [action.section for action in record.actions.values()]
    box = engine.boxes[record.cache_id]
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    poll(game, engine)
    filled = progress(lua, game).stashes.records[1]
    assert filled.next_action == len(filled.actions) + 1
    assert engine.spawn_calls == len(original_sections)
    assert [action.section for action in filled.actions.values()] == original_sections
    assert not record.actions[1].created_id  # Save copies do not alias live plans.
    game.load_state(saved_state(lua, game))
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    poll(game, engine)
    assert engine.spawn_calls == len(original_sections)


def test_only_actual_package_item_acquisition_claims_it_and_preserves_native_markers(lua):
    game, engine = stash_game(lua)
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    box = engine.boxes[record.cache_id]
    engine.markers[f"{record.cache_id}:treasure"] = "native loot"
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    action = record.actions[1]
    factory = lua.eval("""function(id,name,section) return {
        id=function() return id end,name=function() return name end,
        section=function() return section end
    } end""")
    wrong = factory(action.created_id, "wrong", action.section)
    game.actor_on_item_take_from_box(box, wrong)
    assert not progress(lua, game).stashes.records[1].claimed
    item = factory(action.created_id, action.created_name, action.section)
    game.actor_on_item_take_from_box(engine.boxes[(record.cache_id % 3) + 1], item)
    assert not progress(lua, game).stashes.records[1].claimed
    game.actor_on_item_take(item)
    assert progress(lua, game).stashes.records[1].claimed
    poll(game, engine)
    assert not engine.markers[f"{record.cache_id}:gamma_ap_loot"]
    assert engine.markers[f"{record.cache_id}:treasure"] == "native loot"
    game.actor_on_item_take_from_box(box, item)


def test_marker_failure_retries_the_same_plan_and_wrong_pending_item_is_refused(lua):
    game, engine = stash_game(lua)
    engine.fail_marker = True
    poll(game, engine)
    earlier = saved_state(lua, game)
    record = earlier.gamma_archipelago_v1.stashes.records[1]
    assert earlier.gamma_archipelago_v1.received_count == 0
    engine.fail_marker = False
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = encode_incoming(
        KEY, (FIRST + 1,), earlier.gamma_archipelago_v1.configuration_key
    )
    poll(game, engine)
    assert "Conflicting pending" in list(engine.logs.values())[-1]
    assert progress(lua, game).received_count == 0
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = encode_incoming(
        KEY, (FIRST,), earlier.gamma_archipelago_v1.configuration_key
    )
    game.load_state(earlier)
    poll(game, engine)
    assert progress(lua, game).stashes.records[1].cache_id == record.cache_id
    assert progress(lua, game).received_count == 1


def test_missing_or_unowned_roster_waits_without_blocking_map_checks(lua):
    game, engine = stash_game(lua)
    for server in engine.servers.values():
        server.parent_id = 0
    poll(game, engine)
    assert "roster to initialize" in list(engine.logs.values())[-1]
    assert progress(lua, game).checks[28052001]
    assert progress(lua, game).received_count == 0
    lua.globals().treasure_manager = None
    poll(game, engine)
    lua.globals().treasure_manager = lua.table(caches=False)
    poll(game, engine)


@pytest.mark.parametrize("field,value", [("parent_id", 0), ("m_game_vertex_id", "l05_bar")])
def test_recorded_cache_identity_changes_never_select_a_replacement(lua, field, value):
    game, engine = stash_game(lua)
    poll(game, engine)
    state = progress(lua, game)
    record = state.stashes.records[1]
    engine.servers[record.cache_id][field] = value
    poll(game, engine)
    assert "will not reroll" in list(engine.logs.values())[-1]
    assert progress(lua, game).stashes.records[1].cache_id == record.cache_id


def test_bounded_spawning_nil_retries_and_offline_box_waits(lua):
    game, engine = stash_game(lua, items=(ADVANCED,))
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    box = engine.boxes[record.cache_id]
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    engine.boxes[record.cache_id] = None
    poll(game, engine)
    assert engine.spawn_calls == 0
    engine.boxes[record.cache_id] = box
    engine.fail_spawn = True
    poll(game, engine)
    assert progress(lua, game).stashes.records[1].next_action == 1
    engine.fail_spawn = False
    engine.game_object_result = True
    before = engine.spawn_calls
    poll(game, engine)
    assert engine.spawn_calls - before == 8
    assert progress(lua, game).stashes.records[1].next_action == 9
    poll(game, engine)
    assert progress(lua, game).stashes.records[1].next_action == 10


@pytest.mark.parametrize("failure", ["raise_spawn", "bad_identity"])
def test_uncertain_creation_never_automatically_spawns_a_second_copy(lua, failure):
    game, engine = stash_game(lua)
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    engine[failure] = True
    poll(game, engine)
    assert progress(lua, game).stashes.records[1].actions[1].uncertain
    calls = engine.spawn_calls
    engine[failure] = False
    game.load_state(saved_state(lua, game))
    poll(game, engine)
    assert engine.spawn_calls == calls


def test_dxml_and_section_capabilities_are_required_before_acknowledging_coordinates(lua):
    game, engine = stash_game(lua)
    lua.globals().modxml_gamma_ap_stashes = None
    poll(game, engine)
    assert "DXML" in list(engine.logs.values())[-1]
    lua.globals().modxml_gamma_ap_stashes = lua.table(
        registered=True, ready=lua.eval("function() return true end")
    )
    engine.missing_section = "bandage"
    poll(game, engine)
    assert "loot section is unavailable" in list(engine.logs.values())[-1]
    assert progress(lua, game).received_count == 0


@pytest.mark.parametrize("capability", [None, "false", "nil", "string"])
def test_registered_hook_without_marker_definitions_never_calls_native_map_api(lua, capability):
    game, engine = stash_game(lua)
    lua.execute("""
        engine.map_calls=0
        level.map_add_object_spot_ser=function()
            engine.map_calls=engine.map_calls+1
        end
    """)
    lua.globals().modxml_gamma_ap_stashes.ready = (
        None
        if capability is None
        else lua.eval(
            "function() return "
            + {"false": "false", "nil": "nil", "string": "'ready'"}[capability]
            + " end"
        )
    )
    poll(game, engine)
    assert engine.map_calls == 0
    assert progress(lua, game).received_count == 0


def test_saved_stash_waits_for_verified_definitions_before_map_calls_or_spawning(lua):
    game, engine = stash_game(lua)
    poll(game, engine)
    earlier = saved_state(lua, game)
    record = earlier.gamma_archipelago_v1.stashes.records[1]
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    stored = saved_state(lua, game)
    lua.globals().modxml_gamma_ap_stashes.ready = lua.eval("function() return false end")
    lua.execute("""
        engine.map_calls=0
        level.map_has_object_spot=function() engine.map_calls=engine.map_calls+1; return 0 end
        level.map_add_object_spot_ser=function() engine.map_calls=engine.map_calls+1 end
    """)
    game.load_state(stored)
    poll(game, engine)
    state = progress(lua, game)
    assert engine.map_calls == 0 and engine.spawn_calls == 0
    assert state.received_count == 1 and state.stashes.records[1].next_action == 1
    assert state.stashes.records[1].cache_id == record.cache_id
    lua.globals().modxml_gamma_ap_stashes.ready = lua.eval("function() return true end")
    poll(game, engine)
    assert engine.spawn_calls == len(record.actions) and engine.map_calls > 0
    game.load_state(saved_state(lua, game))
    poll(game, engine)
    assert engine.spawn_calls == len(record.actions)


def test_disabled_unbound_and_bounded_receipts_are_refused(lua):
    game, _ = stash_game(lua)
    state = lua.globals().gamma_ap_state.new_state()
    module = lua.globals().gamma_ap_stashes
    assert module.receive(state, FIRST)[0] is False
    module.open(state, None, None)
    module.take(state, None, None)
    assert module.poll(state) is True
    state.session_key = KEY
    state.expanded = True
    assert module.receive(state, FIRST)[0] is False
    state.allowed_items[FIRST] = True
    state.allowed_items[42] = True
    assert module.receive(state, 42)[0] is False
    state.received_count = 4000
    state.stashes.order = lua.table_from(range(1, 4001))
    assert "bound" in module.receive(state, FIRST)[1]


def test_progression_coordinates_require_the_fixed_box_and_deliver_protected_helmet(lua):
    game, engine = stash_game(lua, items=(28051201,), rewards_progression_stashes=1)
    poll(game, engine)
    assert progress(lua, game).received_count == 0
    assert not list(engine.spawns.values())
    lua.globals().make_cache(30, "esc_treasure_3", "l01_escape", 65535, "invbox")
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    assert record.cache_id == 30 and not record.claimed
    assert engine.markers["30:gamma_ap_progression"]
    game.physic_object_on_use_callback(engine.boxes[1], lua.globals().db.actor)
    poll(game, engine)
    assert not list(engine.spawns.values())
    game.physic_object_on_use_callback(engine.boxes[30], lua.globals().db.actor)
    engine.fail_spawn = True
    poll(game, engine)
    assert not progress(lua, game).stashes.records[1].claimed
    engine.fail_spawn = False
    poll(game, engine)
    assert progress(lua, game).stashes.records[1].claimed
    assert not engine.markers["30:gamma_ap_progression"]
    item = next(iter(engine.spawns.values()))
    assert item.section == "good_psy_helmet" and item.owner == 0
    calls = engine.spawn_calls
    game.load_state(saved_state(lua, game))
    poll(game, engine)
    assert engine.spawn_calls == calls
