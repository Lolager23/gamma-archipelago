from collections import Counter

from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.progression_readiness import allowed, requirements


def configuration(**options):
    return build_configuration(
        defaults()
        | {
            "rewards_starting_gear_unlocks": 1,
            "rewards_progressive_tools": 1,
            "rewards_recipe_access": 1,
        }
        | options
    )


def test_scorcher_and_path_pripyat_need_their_equipment_classes_and_tools():
    config = configuration()
    count = Counter({"Progressive Firearm Class": 2, "Progressive Outfit Class": 2})
    row = {"readiness": {"firearms": 3, "outfit": 3, "tools": 2}}
    assert requirements(config, row) == row["readiness"]
    assert allowed(config, row, count.__getitem__, lambda _: True, 2)
    for name in count:
        count[name] -= 1
        assert not allowed(config, row, count.__getitem__, lambda _: True, 2)
        count[name] += 1
    assert not allowed(config, row, count.__getitem__, lambda _: True, 1)
    path = {"readiness": {"firearms": 4, "outfit": 4, "tools": 3}}
    assert not allowed(config, path, count.__getitem__, lambda _: True, 3)
    count.update({"Progressive Firearm Class": 1, "Progressive Outfit Class": 1})
    assert allowed(config, path, count.__getitem__, lambda _: True, 3)
    assert allowed(
        configuration(rewards_progressive_tools=0), path, count.__getitem__, lambda _: True, 0
    )
    assert allowed(
        configuration(regional_progression=0), path, Counter().__getitem__, lambda _: False, 0
    )
    assert requirements(configuration(regional_progression=0), path) == {}


def test_machinegun_and_exoskeleton_checks_require_shutdown_and_red_forest_plus_another_region():
    row = {"northern_readiness": True}
    config = configuration()
    count = Counter()
    assert not allowed(config, row, count.__getitem__, lambda _: True, 0)
    count["Brain Scorcher Disabled"] = 1
    assert not allowed(config, row, count.__getitem__, {"l10_red_forest"}.__contains__, 0)
    assert not allowed(config, row, count.__getitem__, {"jupiter"}.__contains__, 0)
    assert allowed(config, row, count.__getitem__, {"l10_red_forest", "jupiter"}.__contains__, 0)
    assert allowed(
        config, row, count.__getitem__, {"l10_red_forest", "l10_limansk"}.__contains__, 0
    )


def test_artefact_recipe_permission_applies_from_twenty_one_including_overflow():
    config = configuration()
    count = Counter()
    assert allowed(
        config, {"quota_group": "artefact", "minimum": 20}, count.__getitem__, lambda _: True, 0
    )
    for total in (21, 40, 60):
        row = {"quota_group": "artefact", "minimum": total}
        assert not allowed(config, row, count.__getitem__, lambda _: True, 0)
        assert allowed(
            configuration(rewards_recipe_access=0), row, count.__getitem__, lambda _: True, 0
        )
        count["Recipe Access: Artefacts"] = 1
        assert allowed(config, row, count.__getitem__, lambda _: True, 0)
        count.clear()
