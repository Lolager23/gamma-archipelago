from pathlib import Path
from xml.etree import ElementTree

import pytest

from gamma_archipelago.protocol import encode_incoming

from .test_game_adapter import enter_world, saved_state
from .test_loadout import KEY
from .test_stashes import poll, progress, stash_game

PSI = 28051201
TEMPLATE = 'Archipelago stash: "{item}" was delivered directly to your inventory.'


def protected_stash(lua, items=(PSI,), **options):
    game, engine = stash_game(lua, items=items, rewards_progression_stashes=1, **options)
    box = lua.globals().make_cache(30, "esc_treasure_3", "l01_escape", 65535, "invbox")
    for _ in items:
        poll(game, engine)
    lua.execute("""
        translations={st_psi_name='Calibrated Psi Helmet'}
        game=game or {}
        game.translate_string=function(key) return translations[key] or key end
        engine.meta.good_psy_helmet={inv_name='st_psi_name'}
    """)
    return game, engine, box


def test_successful_direct_delivery_announces_once_and_saved_reload_never_respawns(lua):
    game, engine, box = protected_stash(lua)
    assert not list(engine.stash_news.values())
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    record = progress(lua, game).stashes.records[1]
    assert record.claimed and record.inventory_notice_pending
    assert engine.spawn_calls == 1 and engine.spawns[101].owner == 0
    poll(game, engine)
    assert list(engine.stash_news.values()) == [TEMPLATE.format(item="Calibrated Psi Helmet")]
    assert not progress(lua, game).stashes.records[1].inventory_notice_pending
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    poll(game, engine)
    game.load_state(saved_state(lua, game))
    enter_world(engine)
    poll(game, engine)
    assert len(engine.stash_news) == engine.spawn_calls == 1


def test_pending_notice_survives_reload_and_waits_for_world_readiness(lua):
    game, engine, box = protected_stash(lua)
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    game.load_state(saved_state(lua, game))
    poll(game, engine)
    assert not list(engine.stash_news.values())
    assert progress(lua, game).stashes.records[1].inventory_notice_pending
    enter_world(engine)
    engine.paused = True
    poll(game, engine)
    assert not list(engine.stash_news.values())
    engine.paused = False
    poll(game, engine)
    assert len(engine.stash_news) == engine.spawn_calls == 1


def test_display_failure_retries_only_notice_and_does_not_hold_later_rewards(lua):
    game, engine, box = protected_stash(lua)
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    calls = engine.spawn_calls
    state = progress(lua, game)
    engine.files["D:/AnomalyAP/appdata/archipelago\\incoming.txt"] = encode_incoming(
        KEY, (PSI, 28051003), state.configuration_key
    )
    engine.fail_stash_notice = True
    poll(game, engine)
    assert not list(engine.stash_news.values())
    assert progress(lua, game).stashes.records[1].inventory_notice_pending
    assert progress(lua, game).received_count == 2
    assert engine.spawn_calls == calls + 1
    assert sum(item.section == "good_psy_helmet" for item in engine.spawns.values()) == 1
    assert "already delivered" in list(engine.logs.values())[-1]
    engine.fail_stash_notice = False
    poll(game, engine)
    assert len(engine.stash_news) == 1 and engine.spawn_calls == calls + 1


@pytest.mark.parametrize("failure", ["fail_spawn", "raise_spawn"])
def test_failed_or_uncertain_creation_does_not_announce_success(lua, failure):
    game, engine, box = protected_stash(lua)
    engine[failure] = True
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    assert not record.claimed and not record.inventory_notice_pending
    assert not list(engine.stash_news.values())


def test_old_claimed_stash_without_notice_flag_does_not_replay_old_delivery(lua):
    game, engine, box = protected_stash(lua)
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    data = saved_state(lua, game)
    data.gamma_archipelago_v1.stashes.records[1].inventory_notice_pending = None
    game.load_state(data)
    enter_world(engine)
    poll(game, engine)
    assert engine.spawn_calls == 1 and not list(engine.stash_news.values())


def test_ordinary_box_loot_does_not_emit_a_direct_inventory_notice(lua):
    game, engine = stash_game(lua)
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    poll(game, engine)
    assert not list(engine.stash_news.values())


def test_map_cleanup_failure_cannot_hide_an_already_delivered_inventory_reward(lua):
    game, engine, box = protected_stash(lua)
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    engine.servers[30] = None
    poll(game, engine)
    assert len(engine.stash_news) == 1
    poll(game, engine)
    assert len(engine.stash_news) == engine.spawn_calls == 1


def test_two_direct_deliveries_are_announced_at_most_one_per_poll(lua):
    game, engine, box = protected_stash(lua, items=(PSI, PSI))
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    poll(game, engine)
    assert len(engine.stash_news) == 1
    poll(game, engine)
    assert len(engine.stash_news) == 2 and engine.spawn_calls == 2


@pytest.mark.parametrize("template", [None, "", "{item}{item}", "{unknown}", "%c[red]{item}"])
def test_invalid_or_missing_translation_uses_complete_english_fallback(lua, template):
    _, _, _ = protected_stash(lua)
    lua.globals().translations.gamma_ap_stash_inventory_delivery = template
    assert lua.globals().gamma_ap_notice_text.stash_inventory(PSI) == TEMPLATE.format(
        item="Calibrated Psi Helmet"
    )


def test_selected_language_and_native_item_label_are_used_without_recursive_substitution(lua):
    _, _, _ = protected_stash(lua)
    lua.globals().translations.st_psi_name = "{item}"
    lua.globals().translations.gamma_ap_stash_inventory_delivery = 'Inventory: "{item}".'
    assert lua.globals().gamma_ap_notice_text.stash_inventory(PSI) == 'Inventory: "{item}".'


def test_missing_native_metadata_falls_back_to_owned_reward_translation_then_catalogue(lua):
    _, engine, _ = protected_stash(lua)
    engine.meta.good_psy_helmet = None
    lua.globals().translations.gamma_ap_reward_28051201 = "Translated psi reward"
    module = lua.globals().gamma_ap_notice_text
    assert module.stash_inventory(PSI) == TEMPLATE.format(item="Translated psi reward")
    lua.globals().translations.gamma_ap_reward_28051201 = "%c[red]"
    assert module.stash_inventory(PSI) == TEMPLATE.format(
        item="Progression Stash: Calibrated Psi Helmet"
    )
    lua.globals().ini_sys = None
    assert "Progression Stash: Calibrated Psi Helmet" in module.stash_inventory(PSI)
    assert "Basic Loot Stash: Supplies" in module.stash_inventory(28051101)


@pytest.mark.parametrize("change", ["type", "unclaimed", "unfinished", "ordinary"])
def test_saved_notice_flag_cannot_claim_an_undelivered_or_ordinary_reward(lua, change):
    game, _, box = protected_stash(lua)
    game.physic_object_on_use_callback(box, lua.globals().db.actor)
    state = progress(lua, game)
    record = state.stashes.records[1]
    if change == "type":
        record.inventory_notice_pending = "yes"
    elif change == "unclaimed":
        record.claimed = False
    elif change == "unfinished":
        record.next_action = 1
    else:
        lua.globals().gamma_ap_catalog.protected_stash_items[PSI] = None
    assert lua.globals().gamma_ap_save_validation.validate(state)[0] is False


def test_translation_resource_contains_the_exact_fallback_template():
    path = (
        Path(__file__).resolve().parents[2]
        / "mod/gamedata/configs/text/eng/st_gamma_ap_stashes.xml"
    )
    entries = {
        node.attrib["id"]: node.findtext("text") for node in ElementTree.parse(path).getroot()
    }
    assert entries["gamma_ap_stash_inventory_delivery"] == TEMPLATE
