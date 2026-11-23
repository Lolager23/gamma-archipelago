import json
from pathlib import Path

import pytest

from .test_game_adapter import saved_state
from .test_loadout import KEY
from .test_stashes import FIRST, poll, progress, stash_game

DATA = json.loads((Path(__file__).parents[2] / "src/gamma_archipelago/catalog.json").read_text())
STASHES = [row for row in DATA["items"] if "loot_roll_v1" in row]


@pytest.mark.parametrize("row", STASHES, ids=lambda row: row["name"])
def test_tiered_rolls_vary_quantities_and_contents_without_changing_calibre_or_global_rng(lua, row):
    lua.execute("math.random=function() error('AP must not consume the game RNG') end")
    module = lua.globals().gamma_ap_stash_loot
    rule = row["loot_roll_v1"]
    profile = DATA["stash_loot_profiles_v1"][rule["profile"]]
    shapes, sizes = set(), set()
    for receipt in range(1, 51):
        sections = tuple(module.sections(KEY, row["id"], receipt, 1).values())
        assert sections == tuple(module.sections(KEY, row["id"], receipt, 1).values())
        supplies = [section for section in sections if not section.startswith("ammo_")]
        ammo = [section for section in sections if section.startswith("ammo_")]
        assert profile["minimum"] <= len(supplies) <= profile["maximum"]
        assert set(supplies) <= set(profile["supplies"]) | set(profile["quality"])
        assert set(supplies) & set(profile["quality"])
        assert set(ammo) <= set(rule["ammunition"])
        if rule["ammunition"]:
            assert profile["ammo_minimum"] <= len(ammo) <= profile["ammo_maximum"]
        else:
            assert not ammo
        shapes.add(sections)
        sizes.add(len(sections))
    assert len(shapes) >= 20 and len(sizes) >= 3


def test_roll_uses_full_session_key_and_does_not_randomize_progression_contents(lua):
    module = lua.globals().gamma_ap_stash_loot
    assert tuple(module.sections(KEY, FIRST, 1, 1).values()) != tuple(
        module.sections(KEY[:-1] + "b", FIRST, 1, 1).values()
    )
    assert list(module.sections(KEY, 28051201, 1, None).values()) == ["good_psy_helmet"]
    assert module.sections(KEY, 28051201, 1, 1) is None
    assert module.sections(KEY, FIRST, 1, 2) is None
    for key in (None, "", "x" * 64):
        assert module.sections(key, FIRST, 1, 1) is None


def test_randomized_plan_is_saved_before_open_and_keeps_created_actions_through_retry(lua):
    game, engine = stash_game(lua, randomized_stash_loot=1)
    poll(game, engine)
    record = progress(lua, game).stashes.records[1]
    expected = [action.section for action in record.actions.values()]
    assert record.loot_version == 1 and not record.opened
    game.load_state(saved_state(lua, game))
    assert [
        action.section for action in progress(lua, game).stashes.records[1].actions.values()
    ] == expected
    engine.fail_spawn = True
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    assert engine.spawn_calls == 1 and not list(engine.spawns)
    game.load_state(saved_state(lua, game))
    engine.fail_spawn = False
    poll(game, engine)
    while progress(lua, game).stashes.records[1].next_action <= len(expected):
        poll(game, engine)
    actual = [spawn.section for spawn in engine.spawns.values()]
    assert sorted(actual) == sorted(expected)
    calls = engine.spawn_calls
    game.load_state(saved_state(lua, game))
    game.physic_object_on_use_callback(engine.boxes[record.cache_id], lua.globals().db.actor)
    poll(game, engine)
    assert engine.spawn_calls == calls


def test_legacy_assigned_stashes_load_unchanged_when_randomization_is_enabled(lua):
    game, engine = stash_game(lua, randomized_stash_loot=1)
    poll(game, engine)
    saved = saved_state(lua, game)
    record = saved.gamma_archipelago_v1.stashes.records[1]
    record.loot_version = None
    record.actions = lua.table_from(
        [lua.table(section=section) for section in STASHES[0]["contents"]]
    )
    game.load_state(saved)
    restored = progress(lua, game)
    assert not restored.refused_save and restored.received_count == 1
    record = restored.stashes.records[1]
    assert record.loot_version is None
    assert [action.section for action in record.actions.values()] == STASHES[0]["contents"]


@pytest.mark.parametrize(
    "mutation",
    ["record.loot_version=2", "record.actions[1].section='unapproved'", "record.actions[1]=nil"],
)
def test_randomized_plan_tampering_is_rejected_before_mutation(lua, mutation):
    game, engine = stash_game(lua, randomized_stash_loot=1)
    poll(game, engine)
    state = progress(lua, game)
    lua.globals().record = state.stashes.records[1]
    lua.execute(mutation)
    assert lua.globals().gamma_ap_save_validation.validate(state)[0] is False


def test_missing_rolled_section_keeps_receipt_pending_without_reroll(lua):
    game, engine = stash_game(lua, randomized_stash_loot=1)
    sections = lua.globals().gamma_ap_stash_loot.sections(KEY, FIRST, 1, 1)
    engine.missing_section = sections[1]
    poll(game, engine)
    state = progress(lua, game)
    assert state.received_count == 0 and not list(state.stashes.order)
    engine.missing_section = None
    poll(game, engine)
    assert [a.section for a in progress(lua, game).stashes.records[1].actions.values()] == list(
        sections.values()
    )
