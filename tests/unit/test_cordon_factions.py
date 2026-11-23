import json
from importlib.resources import files

from gamma_archipelago.activity_requirements import regional_requirement
from gamma_archipelago.configuration import build_configuration
from gamma_archipelago.presets import presets

ROWS = {
    row["id"]: row
    for row in json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text())[
        "locations"
    ]
}


def test_cordon_has_two_dependable_faction_types_without_the_military_checkpoint():
    config = build_configuration(presets()["living_legend"])

    def cordon(where):
        return where == "l01_escape"

    assert regional_requirement(ROWS[28140102], config).accessible(cordon)
    assert not regional_requirement(ROWS[28140103], config).accessible(cordon)
    assert not regional_requirement(ROWS[28052308], config).accessible(cordon)
    assert regional_requirement(ROWS[28052308], config).accessible(
        lambda where: where == "l03_agroprom"
    )
    names = {
        row["key"]
        for row in ROWS.values()
        if row.get("category") == "checks_faction_first_kills"
        and "logic" in row
        and "l01_escape" in row["logic"]["any_regions"]
    }
    assert names == {"stalker", "bandit"}


def test_other_reachable_sources_and_explicit_exclusions_still_control_faction_quotas():
    config = build_configuration(presets()["living_legend"])

    def swamps(where):
        return where in {"l01_escape", "k00_marsh"}

    assert regional_requirement(ROWS[28140104], config).accessible(swamps)
    excluded = build_configuration(
        config.to_values() | {"discovery_exclusions": ["faction:stalker"]}
    )
    assert not regional_requirement(ROWS[28140102], excluded).accessible(
        lambda where: where == "l01_escape"
    )
