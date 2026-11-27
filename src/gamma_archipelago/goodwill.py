"""Shared goodwill credits each faction separately; legacy rewards retain their meaning."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

SHARED_ID = 28051309
SHARED_NAME = "Faction Goodwill: All Factions"


def shared(configuration: SeedConfiguration) -> bool:
    return bool(
        configuration.option("shared_faction_goodwill")
        and "rewards_faction_reputation" in configuration.rewards
    )


def copies(configuration: SeedConfiguration, name: str, count: Callable[[str], int]) -> int:
    common = count(SHARED_NAME) if shared(configuration) else 0
    return common if name == SHARED_NAME else count(name) + common


def pool_name(configuration: SeedConfiguration, name: str) -> str:
    return SHARED_NAME if shared(configuration) else name
