"""Public protected-opening guarantees; reliable checks never depend on random encounters."""

import json
from collections.abc import Mapping
from importlib.resources import files
from typing import TYPE_CHECKING

from .catalog import MAP_LOCATIONS

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

_catalog = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
CORDON_CHECKS = frozenset(
    row["id"]
    for row in _catalog["locations"]
    if row["level"] == "l01_escape" and row["category"] in {"checks_maps", "checks_settlements"}
)


def opening_permissions(
    configuration: "SeedConfiguration", starting: Mapping[str, int]
) -> tuple[str, ...]:
    if not configuration.option("opening_policy"):
        return ()
    gear = dict(configuration.gear)
    groups = []
    if gear["starting_pda"] == 2:
        groups.append("PDA")
    if gear["starting_detector"] == 2 and "checks_artefacts" in configuration.checks:
        groups.append("Detector")
    fight = bool(
        configuration.checks
        & {"checks_mutant_first_kills", "checks_faction_first_kills", "checks_kill_milestones"}
    ) or configuration.goal not in {"pilot_tour", "psi_protection"}
    if (
        fight
        and gear["starting_firearms"] == 2
        and (configuration.option("combat_logic") > 0 or gear["starting_melee"] == 2)
    ):
        groups.append("Firearms")
    return tuple(
        "Equipment Unlock: " + group
        for group in groups
        if not starting.get("Equipment Unlock: " + group, 0)
    )


def opening_checks(
    check_ids: frozenset[int], excluded: frozenset[int], zone_keys_remaining: bool
) -> frozenset[int]:
    ids = (check_ids - excluded) & CORDON_CHECKS
    return ids - {MAP_LOCATIONS["l01_escape"]} if zone_keys_remaining else ids
