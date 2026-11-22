import json
from pathlib import Path

from gamma_archipelago.activity_requirements import regional_requirement, unreliable_check_ids
from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.discovery import configured_location_ids
from gamma_archipelago.pool_budget import budget_pool
from gamma_archipelago.presets import presets

CATALOG = json.loads((Path(__file__).parents[2] / "src/gamma_archipelago/catalog.json").read_text())
ROWS = {row["id"]: row for row in CATALOG["locations"]}


def config(**values):
    return build_configuration({**defaults(), **values})


def test_catalogue_covers_every_global_activity_without_all_zone_fallbacks():
    levels = {row["id"] for row in CATALOG["levels"]}
    for row in ROWS.values():
        if row["level"] == "Menu":
            assert (
                "logic" in row
                or "quota_group" in row
                or row["category"] in CATALOG["activity_regions"]
            )
        rule = regional_requirement(row, config())
        assert all(set(source) <= levels for source in rule.sources)
        assert set(rule.all_regions) <= levels
    for category in CATALOG["milestones"]:
        assert regional_requirement({"category": category}, config()).accessible(
            lambda level: level == "l01_escape"
        )


def test_individual_sources_require_any_documented_region_and_story_requires_its_prefix():
    boar = regional_requirement(ROWS[28052202], config())
    assert boar.accessible(lambda region: region == "l01_escape")
    assert not boar.accessible(lambda region: False)
    doctor = regional_requirement(ROWS[28052601], config())
    assert not doctor.accessible(lambda region: region == "l01_escape")
    assert doctor.accessible(lambda region: region in {"l01_escape", "k00_marsh"})
    assert not regional_requirement(ROWS[28052602], config()).accessible(
        lambda region: region in {"l01_escape", "k00_marsh"}
    )
    assert regional_requirement(ROWS[28052001], config()).accessible(lambda region: False)


def test_generic_quotas_count_types_and_respect_exclusions_and_unverified_rosters():
    options = config(
        mutant_discovery_mode=1, checks_mutant_first_kills=1, mutant_discovery_count=25
    )
    first = regional_requirement(ROWS[28140001], options)
    assert first.accessible(lambda region: region == "l01_escape")
    assert not first.accessible(lambda region: False)
    cordon_types = [
        row
        for row in ROWS.values()
        if row["category"] == "checks_mutant_first_kills"
        and "logic" in row
        and row["logic"]["reliable"]
        and "l01_escape" in row["logic"]["any_regions"]
    ]
    following = regional_requirement(ROWS[28140001 + len(cordon_types)], options)
    assert not following.accessible(lambda region: region == "l01_escape")
    excluded = config(
        checks_mutant_first_kills=1,
        mutant_discovery_mode=1,
        mutant_discovery_count=1,
        discovery_exclusions=["mutant:" + row["key"] for row in cordon_types],
    )
    assert not regional_requirement(ROWS[28140001], excluded).accessible(
        lambda region: region == "l01_escape"
    )
    excess = regional_requirement(ROWS[28140025], options)
    assert not excess.reliable and excess.accessible(lambda region: True)
    no_sources = config(
        discovery_exclusions=[
            "mutant:" + row["key"]
            for row in ROWS.values()
            if row["category"] == "checks_mutant_first_kills"
            and "logic" in row
            and row["logic"]["reliable"]
        ]
    )
    assert not regional_requirement(ROWS[28140001], no_sources).reliable
    assert regional_requirement(ROWS[28140001], no_sources).accessible(lambda region: False)


def test_unknown_sources_and_quota_excess_reserve_filler_before_pool_budgeting():
    options = build_configuration(presets()["full_story"])
    unsafe = unreliable_check_ids(options)
    assert {28052223, 28052401, 28052412} <= unsafe
    ids = configured_location_ids(options)
    budget = budget_pool(options, ids)
    assert budget.eligible_checks <= len(ids - unsafe)
    assert not regional_requirement(ROWS[28052401], options).reliable
    assert regional_requirement(ROWS[28052401], options).accessible(lambda region: False)
