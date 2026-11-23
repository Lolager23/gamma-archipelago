"""Real placement constraints, not merely deferred calculator rewards."""

from collections import Counter

import pytest
from Fill import distribute_items_restrictive, swap_location_item
from Options import OptionError
from test.general import setup_multiworld
from worlds.apquest.world import APQuestWorld
from worlds.gamma import GammaWorld
from worlds.gamma import sphere_pacing as pacing

from gamma_archipelago.configuration import build_configuration, defaults, encode_configuration
from gamma_archipelago.presets import presets


def filled(seed=83, name="living_legend", **changes):
    multi = setup_multiworld(GammaWorld, options=presets()[name] | changes, seed=seed)
    distribute_items_restrictive(multi)
    return multi


def inventory(multi):
    return Counter((row.item.player, row.item.name) for row in multi.get_filled_locations())


@pytest.mark.parametrize("name", ["living_legend", "full_story"])
@pytest.mark.parametrize("seed", [83, 260, 20261122])
def test_actual_raw_spheres_have_one_progressive_receipt_per_chain(name, seed):
    multi = filled(seed, name)
    before = inventory(multi)
    reachable_before = pacing._trace(multi, {1}).waves
    fixed = {row: row.item for row in multi.get_filled_locations() if row.locked}
    GammaWorld.stage_finalize_multiworld(multi)
    GammaWorld.stage_pre_output(multi)
    trace = pacing._trace(multi, {1})
    assert trace.valid and trace.score == 0
    assert all(reachable_before[model].keys() <= trace.waves[model].keys() for model in trace.waves)
    actual = {row: number for number, sphere in enumerate(multi.get_spheres(), 1) for row in sphere}
    assert trace.waves["upstream"] == actual
    assert inventory(multi) == before and all(row.item is item for row, item in fixed.items())
    assert all(row.item.location is row for row in multi.get_filled_locations())
    assert all(row.locked for row in multi.get_filled_locations() if pacing._progressive(row, {1}))


def test_pacing_is_repeatable_and_disabled_legacy_does_not_mutate_any_placement():
    def placements(multi):
        return {
            (row.player, row.name): (row.item.player, row.item.name)
            for row in multi.get_filled_locations()
        }

    a, b = filled(), filled()
    pacing.pace(a)
    pacing.pace(b)
    assert placements(a) == placements(b)
    old = filled(progressive_sphere_pacing=0)
    before = placements(old)
    pacing.pace(old)
    pacing.validate(old)
    assert placements(old) == before


def test_impossible_depth_fails_and_restores_items_and_locks_atomically():
    multi = filled()
    for region in multi.get_regions():
        for entrance in region.entrances:
            entrance.access_rule = lambda state: True
    for location in multi.get_locations():
        location.access_rule = lambda state: True
    before = {row: (row.item, row.locked) for row in multi.get_filled_locations()}
    with pytest.raises(OptionError, match="Cannot separate"):
        pacing.pace(multi)
    assert all(
        (row.item, row.locked) == value and row.item.location is row
        for row, value in before.items()
    )


def test_final_validation_refuses_later_balancing_that_reintroduces_collisions():
    multi = filled()
    pacing.pace(multi)
    for region in multi.get_regions():
        for entrance in region.entrances:
            entrance.access_rule = lambda state: True
    for location in multi.get_locations():
        location.access_rule = lambda state: True
    with pytest.raises(OptionError, match="Final placements"):
        pacing.validate(multi)


def test_actual_multiworld_paces_recipient_copies_across_finder_slots():
    from Fill import balance_multiworld_progression

    multi = setup_multiworld(
        [GammaWorld, APQuestWorld], options=presets()["living_legend"], seed=83
    )
    distribute_items_restrictive(multi)
    balance_multiworld_progression(multi)
    GammaWorld.stage_finalize_multiworld(multi)
    pacing.validate(multi)
    assert not pacing._trace(multi, {1}).collisions


def test_trial_must_preserve_even_optional_foreign_reachability():
    from BaseClasses import Location

    multi = filled()
    world = multi.worlds[1]
    trace = pacing._trace(multi, {1})
    # Simulate an optional foreign check present in the incoming reachability
    # model but absent from a trial. Beatable GAMMA goals alone are insufficient.
    extra = Location(2, "Optional foreign check", None)
    for mapping in trace.waves.values():
        mapping[extra] = 1
    before = {row: row.item for row in multi.get_filled_locations()}
    assert pacing._improve(world, [world], trace, {1}) is None
    assert all(row.item is item and item.location is row for row, item in before.items())


def test_equal_collision_counts_prefer_separating_the_earliest_sphere():
    multi = filled()
    trace = pacing._trace(multi, {1})
    assert trace.collisions
    early = trace.collisions[0]
    moved = (*early[:3], early[3] + 1, early[4])
    before = pacing.Trace(trace.waves, [early], trace.valid, trace.state)
    after = pacing.Trace(trace.waves, [moved], trace.valid, trace.state)
    assert before.score == after.score
    assert after.priority < before.priority
    assert pacing.Trace(trace.waves, [], True, trace.state).priority < after.priority


def test_new_option_is_bound_and_missing_saved_option_keeps_legacy_wire_and_digest():
    values = presets()["living_legend"]
    assert values["progressive_sphere_pacing"] == 1
    assert defaults()["progressive_sphere_pacing"] == 0
    old = values | {"progressive_sphere_pacing": 0}
    missing = {key: value for key, value in old.items() if key != "progressive_sphere_pacing"}
    explicit, legacy = build_configuration(old), build_configuration(missing)
    assert explicit.digest == legacy.digest != build_configuration(values).digest
    assert "option|progressive_sphere_pacing" not in encode_configuration("a" * 64, legacy, True)
    assert "option|progressive_sphere_pacing|1" in encode_configuration(
        "a" * 64, build_configuration(values), True
    )


def test_recipe_deadline_and_starting_gifts_are_preserved():
    assert pacing._recipes_on_time([])
    multi = filled()
    world = multi.worlds[1]
    recipe = next(
        row for row in multi.get_filled_locations() if row.item.name == "Recipe Access: Artefacts"
    )
    trace = pacing._trace(multi, {1})
    late = max(
        (row for row in trace.waves["network"] if row.address is not None),
        key=trace.waves["network"].__getitem__,
    )
    swap_location_item(recipe, late, check_locked=False)
    assert not pacing._recipes_on_time([world])
    multi.push_precollected(world.create_item("Recipe Access: Artefacts"))
    assert pacing._recipes_on_time([world])


def test_conflicting_locked_progressive_plando_is_not_rewritten():
    multi = filled()
    assert pacing._trace(multi, {1}).collisions
    for row in multi.get_filled_locations():
        if pacing._progressive(row, {1}):
            row.locked = True
    before = {row: (row.item, row.locked) for row in multi.get_filled_locations()}
    with pytest.raises(OptionError, match="fixed placements"):
        pacing.pace(multi)
    assert all((row.item, row.locked) == value for row, value in before.items())


def test_repair_limit_is_bounded_even_if_a_trial_returns_stale_progress(monkeypatch):
    multi = filled()
    calls = []

    def stale(world, worlds, trace, players):
        calls.append(1)
        return trace

    monkeypatch.setattr(pacing, "_improve", stale)
    with pytest.raises(OptionError, match="Cannot separate"):
        pacing.pace(multi)
    assert len(calls) == 256


def test_item_link_owners_and_synthetic_group_worlds_use_real_player_scope():
    from types import SimpleNamespace

    multi = filled()
    multi.groups[99] = dict(game=GammaWorld.game, players={1}, item_pool={"Progressive Tools"})
    multi.groups[98] = dict(game=APQuestWorld.game, players={1}, item_pool={"Progressive Tools"})
    multi.groups[97] = dict(game=GammaWorld.game, players={1}, item_pool={"Bandage"})
    multi.worlds[99] = SimpleNamespace(game=GammaWorld.game)
    worlds = pacing._worlds(multi)
    assert len(worlds) == 1 and pacing._owners(multi, worlds) == {1, 99}


@pytest.mark.parametrize("item", ["Progressive Backpack", "Progressive Tools"])
def test_real_upstream_item_links_keep_shared_progressive_copies_in_separate_spheres(item):
    from BaseClasses import CollectionState
    from Fill import balance_multiworld_progression
    from test.general import gen_steps

    links = [
        dict(
            name="Shared progressive rewards",
            item_pool=[item],
            replacement_item="Bandage",
            link_replacement=False,
        )
    ]
    multi = setup_multiworld(
        [GammaWorld, GammaWorld],
        steps=gen_steps[:-1],
        options=presets()["living_legend"] | {"item_links": links},
        seed=83,
    )
    multi.set_item_links()
    multi.state = CollectionState(multi)
    multi.link_items()
    for player in multi.player_ids:
        multi.worlds[player].pre_fill()
    distribute_items_restrictive(multi)
    balance_multiworld_progression(multi)
    GammaWorld.stage_finalize_multiworld(multi)
    GammaWorld.stage_pre_output(multi)
    (group,) = multi.groups
    assert group in pacing._owners(multi, pacing._worlds(multi))
    trace = pacing._trace(multi, {1, 2, group})
    assert trace.valid and trace.score == 0 and multi.can_beat_game()


@pytest.mark.parametrize("start", [1, 2, 3])
def test_non_cordon_and_zero_class_starts_keep_real_spheres_and_early_recipes(start):
    multi = filled(
        260,
        starting_location=start,
        initial_firearm_class=0,
        initial_outfit_class=0,
        initial_helmet_class=0,
        initial_backpack_class=0,
    )
    pacing.pace(multi)
    pacing.validate(multi)
    assert pacing._trace(multi, {1}).score == 0
    assert pacing._recipes_on_time([multi.worlds[1]])


@pytest.mark.parametrize("name", list(presets()))
def test_every_default_preset_has_sufficient_actual_progression_depth(name):
    multi = filled(85, name)
    pacing.pace(multi)
    pacing.validate(multi)
