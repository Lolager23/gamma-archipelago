from itertools import combinations

from gamma_archipelago.activity_requirements import RegionalRequirement, regional_requirement
from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.mutant_diversity import capacity
from gamma_archipelago.web_planner import catalogue


def test_cordon_has_three_starting_slots_and_two_per_additional_supported_region():
    sources = (("l01_escape", "k01_darkscape"),) * 10
    cordon = frozenset({"l01_escape"})
    assert capacity(sources, cordon, "l01_escape") == 3
    assert capacity(sources, cordon | {"k01_darkscape"}, "l01_escape") == 5
    assert capacity(sources, cordon | {"no_sources"}, "l01_escape") == 3
    assert capacity(sources, cordon, "k01_darkscape") == 2
    assert capacity(sources, frozenset({"k01_darkscape"}), "k01_darkscape") == 5


def test_cordon_sources_are_boar_flesh_and_dog_and_exclusions_reduce_availability():
    rows = catalogue()["locations"]
    named = [
        row
        for row in rows
        if row["category"] == "checks_mutant_first_kills" and "quota_group" not in row
    ]
    assert {row["key"] for row in named if "l01_escape" in row["logic"]["any_regions"]} == {
        "boar",
        "flesh",
        "dog",
    }
    fresh = build_configuration(defaults())
    excluded = build_configuration(defaults() | {"discovery_exclusions": ["mutant:dog"]})
    for minimum in range(1, 6):
        row = next(r for r in rows if r.get("quota_group") == "mutant" and r["minimum"] == minimum)
        assert regional_requirement(row, fresh).accessible({"l01_escape"}.__contains__) == (
            minimum <= 3
        )
        assert regional_requirement(row, excluded).accessible({"l01_escape"}.__contains__) == (
            minimum <= 2
        )
        assert regional_requirement(row, fresh).accessible(
            {"l01_escape", "k01_darkscape"}.__contains__
        )


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
    assert regional_requirement(generic, legacy).accessible(
        {"l01_escape", "k01_darkscape"}.__contains__
    )
    assert not requirement.accessible({"l01_escape", "k01_darkscape"}.__contains__)
    named = next(
        r for r in rows if r["category"] == "checks_mutant_first_kills" and "quota_group" not in r
    )
    assert regional_requirement(named, fresh).mutant_start == ""
    assert not RegionalRequirement(all_regions=("blocked",), mutant_start="a").accessible(
        lambda _: False
    )
