"""Supported native starts. Random selection belongs to the seeded world RNG."""

import json
from importlib.resources import files
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

STARTS: tuple[dict[str, str], ...] = tuple(
    json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))[
        "starting_locations"
    ]
)


def starting_level(configuration: "SeedConfiguration") -> str:
    index = configuration.option("starting_location") if configuration.option("ap_start") else 0
    # Settings-only previews of Random use Cordon for conservative budgeting;
    # the real generator resolves Random before constructing regions or filling.
    return STARTS[index if index < len(STARTS) else 0]["level"]
