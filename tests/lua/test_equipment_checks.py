import pytest

from gamma_archipelago.configuration import encode_configuration

from .test_game_adapter import saved_state
from .test_loadout import CONFIG_PATH, KEY, configured_game


def equipment_game(lua, **options):
    game, engine, configuration = configured_game(lua, checks_maps=0, **options)
    engine.files[CONFIG_PATH] = encode_configuration(KEY, configuration, expanded=True)
    lua.execute("""
        engine.objects={}
        db.actor.item_in_slot=function(self,slot) return slot==7 and engine.outfit or nil end
        db.actor.active_item=function() return engine.active end
        make_gear=function(id,section,kind,condition)
            engine.meta[section]={kind=kind}
            local object={health=condition, upgrades={}}
            object.id=function() return id end
            object.name=function() return section..tostring(id) end
            object.section=function() return section end
            object.condition=function(self) return self.health end
            object.iterate_installed_upgrades=function(self,fn)
                if engine.fail_upgrade==id then error('upgrade API failed') end
                for _,upgrade in ipairs(self.upgrades) do fn(upgrade) end
            end
            engine.objects[id]=object
            return object
        end
    """)
    game.actor_on_update()
    return game, engine, configuration


def gear(lua, id_=1, section="test_pistol", kind="w_pistol", condition=1, upgrades=()):
    item = lua.globals().make_gear(id_, section, kind, condition)
    item.upgrades = lua.table_from(upgrades)
    return item


def progress(lua, game):
    return saved_state(lua, game).gamma_archipelago_v1


def poll(game, engine):
    engine.now += 1000
    game.actor_on_update()


def test_armour_tiers_require_worn_usable_gear_and_keep_a_saved_high_water_mark(lua):
    game, engine, _ = equipment_game(lua, checks_armour_tiers=1)
    item = gear(lua, section="test_light", kind="o_light", condition=0)
    engine.outfit = item
    poll(game, engine)
    assert not list(progress(lua, game).checks)
    item.health = 1
    poll(game, engine)
    assert progress(lua, game).checks[28052701]
    earlier = saved_state(lua, game)
    engine.outfit = gear(lua, 2, "test_heavy", "o_heavy")
    poll(game, engine)
    assert progress(lua, game).checks[28052703]
    powered = next(iter(lua.globals().gamma_ap_catalog.powered_outfits))
    engine.outfit = gear(lua, 3, powered, "o_heavy")
    poll(game, engine)
    assert all(progress(lua, game).checks[id_] for id_ in range(28052701, 28052705))
    engine.outfit = item
    poll(game, engine)
    assert progress(lua, game).checks[28052704]
    assert not earlier.gamma_archipelago_v1.checks[28052703]
    engine.outfit = gear(lua, 4, "unknown_outfit", "unknown")
    poll(game, engine)
    engine.outfit = None
    poll(game, engine)


def test_all_weapon_classes_and_better_knives_require_the_active_usable_item(lua):
    game, engine, _ = equipment_game(lua, checks_weapon_tiers=1, checks_knife_tiers=1)
    catalogue = lua.globals().gamma_ap_catalog
    item = gear(lua, condition=0)
    engine.active = item
    poll(game, engine)
    assert not list(progress(lua, game).checks)
    for index, (kind, name) in enumerate(catalogue.weapon_kinds.items(), 2):
        engine.active = gear(lua, index, "test_" + name, kind)
        poll(game, engine)
        assert progress(lua, game).checks[catalogue.weapon_locations[name]]
    machinegun = next(iter(catalogue.machineguns))
    engine.active = gear(lua, 20, machinegun, "w_rifle")
    poll(game, engine)
    assert progress(lua, game).checks[catalogue.weapon_locations.machinegun]
    for index, section in enumerate(catalogue.knives, 30):
        engine.active = gear(lua, index, section, "w_melee")
        poll(game, engine)
    assert all(progress(lua, game).checks[id_] for id_ in range(28052721, 28052725))
    engine.active = gear(lua, 99, "unknown_device", "i_quest")
    poll(game, engine)
    engine.active = None
    poll(game, engine)


def test_upgrades_count_new_installations_and_never_looted_or_reinstalled_baselines(lua):
    game, engine, _ = equipment_game(lua, checks_gear_upgrades=1)
    weapon = gear(lua, upgrades=("preinstalled",))
    helmet = gear(lua, 2, "helmet", "o_helmet")
    gear(lua, 3, "quest_item", "i_quest")
    game.actor_on_item_take(weapon)
    game.actor_on_item_take_from_box(None, helmet)
    poll(game, engine)
    assert progress(lua, game).equipment.counts.firearm == 0
    weapon.upgrades[2] = "installed_a"
    # Inventory refresh callbacks must not replace the baseline before comparison.
    game.actor_on_item_take(weapon)
    game.actor_on_item_take_from_box(None, weapon)
    poll(game, engine)
    assert progress(lua, game).equipment.counts.firearm == 1
    earlier = saved_state(lua, game)
    weapon.health = 0.5  # Repair/condition changes alone cannot add an upgrade.
    weapon.upgrades[2] = None
    poll(game, engine)
    weapon.upgrades[2] = "installed_a"
    poll(game, engine)
    assert progress(lua, game).equipment.counts.firearm == 1
    weapon.upgrades = lua.table_from(["preinstalled", "installed_a", "b", "c", "d", "e", "f"])
    helmet.upgrades = lua.table_from(["a", "b", "c", "d", "e", "f"])
    poll(game, engine)
    state = progress(lua, game)
    assert state.equipment.counts.firearm == state.equipment.counts.armour == 5
    assert all(state.checks[id_] for id_ in range(28052731, 28052737))
    assert earlier.gamma_archipelago_v1.equipment.counts.firearm == 1
    assert not earlier.gamma_archipelago_v1.equipment.observed["1:test_pistol1"].b
    poll(game, engine)
    assert not list(progress(lua, game).equipment.observed)
    game.actor_on_item_take(weapon)  # Completed categories need no additional baseline.


def test_bounded_polling_prunes_dropped_gear_and_baselines_reacquisition(lua):
    game, engine, _ = equipment_game(lua, checks_gear_upgrades=1)
    for id_ in range(1, 11):
        gear(lua, id_, "weapon_" + str(id_))
    poll(game, engine)
    assert len(list(progress(lua, game).equipment.observed)) == 8
    assert progress(lua, game).equipment.cursor == 8
    poll(game, engine)
    assert len(list(progress(lua, game).equipment.observed)) == 10
    assert progress(lua, game).equipment.cursor == 0
    old = engine.objects[1]
    engine.objects[1] = None
    poll(game, engine)
    assert not progress(lua, game).equipment.observed["1:weapon_11"]
    old.upgrades[1] = "installed_elsewhere"
    engine.objects[1] = old
    game.actor_on_item_take(old)
    game.actor_on_item_take(old)
    poll(game, engine)
    assert progress(lua, game).equipment.counts.firearm == 0
    game.load_state(saved_state(lua, game))
    assert len(list(progress(lua, game).equipment.observed)) == 10


@pytest.mark.parametrize("upgrades", [[""], [1], ["x" * 129], list(map(str, range(129)))])
def test_invalid_upgrade_api_data_is_refused_without_progress(lua, upgrades):
    game, engine, _ = equipment_game(lua, checks_gear_upgrades=1)
    item = gear(lua, upgrades=upgrades)
    game.actor_on_item_take(item)
    assert "Cannot inspect" in list(engine.logs.values())[-1]
    assert progress(lua, game).equipment.counts.firearm == 0
    game.actor_on_item_take_from_box(None, item)
    poll(game, engine)
    assert not list(progress(lua, game).equipment.observed)


def test_upgrade_api_failure_can_be_retried_and_disabled_categories_do_not_inspect(lua):
    game, engine, _ = equipment_game(lua, checks_gear_upgrades=1)
    item = gear(lua)
    engine.fail_upgrade = 1
    poll(game, engine)
    assert "Cannot inspect" in list(engine.logs.values())[-1]
    engine.fail_upgrade = None
    poll(game, engine)
    assert progress(lua, game).equipment.observed["1:test_pistol1"] is not None
    game.actor_on_item_take(gear(lua, 4, "not_gear", "i_quest"))
    game.actor_on_item_take(None)
    state = lua.globals().gamma_ap_state.new_state()
    module = lua.globals().gamma_ap_equipment_checks
    assert module.acquired(state, item) is True
    state.session_key = KEY
    assert module.acquired(state, item) is True
    state.expanded = True
    assert module.acquired(state, item) is True
    assert module.poll(state, None) is True
    assert module.poll(state, lua.table(expanded=False)) is True


def test_disabled_tier_categories_cannot_leak_other_equipment_checks(lua):
    game, engine, _ = equipment_game(lua, checks_weapon_tiers=1)
    engine.active = gear(lua, section="wpn_knife5", kind="w_melee")
    poll(game, engine)
    assert not list(progress(lua, game).checks)
