from itertools import combinations

from gamma_archipelago.activity_requirements import RegionalRequirement, regional_requirement
from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.mutant_diversity import capacity
from gamma_archipelago.web_planner import catalogue


def test_five_starting_types_and_two_per_supported_new_region_is_a_ceiling():
    sources = tuple(("cordon", "garbage") for _ in range(15))
    assert capacity(sources, frozenset({"cordon"}), "cordon") == 5
    assert capacity(sources, frozenset({"cordon", "garbage"}), "cordon") == 7
    assert capacity(sources, frozenset({"cordon", "garbage", "no_sources"}), "cordon") == 7
    assert capacity(sources, frozenset(), "cordon") == 0
    assert capacity((), frozenset({"cordon"}), "cordon") == 0


def test_matching_reassigns_common_types_to_preserve_a_limited_source():
    sources = (("cordon", "garbage"),) + (("cordon",),) * 6
    assert capacity(sources, frozenset({"cordon", "garbage"}), "cordon") == 6
    assert capacity(sources, frozenset({"cordon"}), "cordon") == 5
    assert capacity(sources, frozenset({"garbage"}), "cordon") == 1


def test_source_counts_are_monotonic_and_do_not_grow_for_repeated_visits():
    sources = (("a", "b"), ("a",), ("b",), ("c",), ("a", "b", "c")) * 3
    for size in range(4):
        for subset in combinations(("a", "b", "c"), size):
            available = frozenset(subset)
            value = capacity(sources, available, "a")
            assert capacity(sources, available, "a") == value
            for region in ("a", "b", "c"):
                assert capacity(sources, available | {region}, "a") >= value


def test_catalogue_generic_mutants_use_capacity_but_named_and_legacy_checks_do_not():
    rows = catalogue()["locations"]
    generic = next(r for r in rows if r.get("quota_group") == "mutant" and r["minimum"] == 6)
    fresh = build_configuration(defaults())
    requirement = regional_requirement(generic, fresh)
    assert requirement.mutant_start == "l01_escape"
    assert not requirement.accessible({"l01_escape"}.__contains__)
    legacy = build_configuration(defaults() | {"regional_progression": 0})
    assert regional_requirement(generic, legacy).accessible({"l01_escape"}.__contains__)
    named = next(
        r for r in rows if r["category"] == "checks_mutant_first_kills" and "quota_group" not in r
    )
    assert regional_requirement(named, fresh).mutant_start == ""
    assert not RegionalRequirement(all_regions=("blocked",), mutant_start="a").accessible(
        lambda _: False
    )
