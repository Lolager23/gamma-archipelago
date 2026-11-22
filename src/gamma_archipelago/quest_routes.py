"""Native northern psi fields require completed shutdowns, not just a helmet."""

import json
from collections.abc import Callable
from importlib.resources import files
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

_catalog = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
NORTHERN_ZONES = frozenset(_catalog["quest_zone_gates"]["northern_levels"])
SHUTDOWNS = tuple(_catalog["quest_zone_gates"]["shutdown_events"])


def allowed(configuration: "SeedConfiguration", level: str, count: Callable[[str], int]) -> bool:
    return bool(
        not configuration.option("quest_zone_logic")
        or level not in NORTHERN_ZONES
        or all(count(name) for name in SHUTDOWNS)
    )
