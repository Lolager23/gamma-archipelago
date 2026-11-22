from gamma_archipelago.configuration import build_configuration, defaults
from gamma_archipelago.opening import CORDON_CHECKS, opening_checks, opening_permissions


def test_protection_targets_only_locked_needed_permissions_and_respects_starting_items():
    values = {
        **defaults(),
        "opening_policy": 1,
        "equipment_class_progression": 0,
        "rewards_starting_gear_unlocks": 1,
        "starting_pda": 2,
        "starting_detector": 2,
        "starting_firearms": 2,
        "starting_melee": 2,
        "checks_artefacts": 1,
        "checks_mutant_first_kills": 1,
    }
    config = build_configuration(values)
    assert opening_permissions(config, {}) == (
        "Equipment Unlock: PDA",
        "Equipment Unlock: Detector",
        "Equipment Unlock: Firearms",
    )
    held = {name: 1 for name in opening_permissions(config, {})}
    assert not opening_permissions(config, held)
    assert not opening_permissions(build_configuration({**values, "opening_policy": 0}), {})
    safe = build_configuration(
        {
            **values,
            "checks_artefacts": 0,
            "checks_mutant_first_kills": 0,
            "starting_melee": 0,
            "starting_pda": 0,
        }
    )
    assert not opening_permissions(safe, {})
    strict = build_configuration({**safe.to_values(), "combat_logic": 1, "goal": 2})
    assert opening_permissions(strict, {}) == ("Equipment Unlock: Firearms",)
    assert 28052001 in opening_checks(CORDON_CHECKS, frozenset(), False)
    assert 28052001 not in opening_checks(CORDON_CHECKS, frozenset(), True)
    assert not opening_checks(CORDON_CHECKS, CORDON_CHECKS, False)
