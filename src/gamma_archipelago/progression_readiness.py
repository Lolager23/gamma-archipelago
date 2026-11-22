"""Additional story and late-equipment requirements shared by AP access rules."""

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from .catalog import POST_RED_FOREST_REGIONS
from .equipment_classes import level

if TYPE_CHECKING:
    from .configuration import SeedConfiguration


def requirements(configuration: "SeedConfiguration", row: Mapping[str, Any]) -> dict[str, int]:
    return dict(row.get("readiness", {})) if configuration.option("regional_progression") else {}


def allowed(
    configuration: "SeedConfiguration",
    row: Mapping[str, Any],
    count: Callable[[str], int],
    reachable: Callable[[str], bool],
    tools: int,
) -> bool:
    if not configuration.option("regional_progression"):
        return True
    needed = requirements(configuration, row)
    for group, minimum in needed.items():
        if group != "tools" and level(configuration, group, count) < minimum:
            return False
    if "rewards_progressive_tools" in configuration.rewards and tools < needed.get("tools", 0):
        return False
    if row.get("northern_readiness") and not (
        count("Brain Scorcher Disabled")
        and reachable("l10_red_forest")
        and any(reachable(region) for region in POST_RED_FOREST_REGIONS)
    ):
        return False
    return not (
        row.get("quota_group") == "artefact"
        and row["minimum"] > 20
        and "rewards_recipe_access" in configuration.rewards
        and not count("Recipe Access: Artefacts")
    )
