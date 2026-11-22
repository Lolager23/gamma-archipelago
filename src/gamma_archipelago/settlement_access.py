"""Free Stalker baseline settlement access; never mutate native faction relations."""

import json
from dataclasses import dataclass
from importlib.resources import files
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .configuration import SeedConfiguration

_catalog = json.loads(files("gamma_archipelago").joinpath("catalog.json").read_text("utf-8"))
_relations = _catalog["settlement_relations"]
_items = {row["id"]: row for row in _catalog["items"]}


@dataclass(frozen=True)
class SettlementRule:
    faction: str
    label: str
    item: int
    name: str
    copies: int
    minimum: int
    neutral: int


def _rule(faction: str) -> SettlementRule:
    definition = _relations["factions"][faction]
    item = _items.get(definition["reward"])
    minimum = _relations["neutral_threshold"] - definition["relation"]
    needed = max(0, minimum - _relations["starting_goodwill"])
    copies = (needed + item["bonus"] - 1) // item["bonus"] if item else 0
    return SettlementRule(
        faction,
        definition["label"],
        definition["reward"],
        item["name"] if item else "",
        copies,
        minimum,
        _relations["neutral_threshold"],
    )


SETTLEMENT_RULES: dict[int, SettlementRule] = {
    row["id"]: _rule(row["hostile_settlement_faction"])
    for row in _catalog["locations"]
    if "hostile_settlement_faction" in row
}
NEUTRALITY_ITEMS: frozenset[str] = frozenset(
    rule.name for rule in SETTLEMENT_RULES.values() if rule.item
)


def requirement(configuration: "SeedConfiguration", id: int | None) -> SettlementRule | None:
    rule = SETTLEMENT_RULES.get(id) if id is not None else None
    if (
        configuration.option("settlement_reputation_logic")
        and "rewards_faction_reputation" in configuration.rewards
        and rule
        and rule.item
    ):
        return rule
    return None


def protected_settlements(configuration: "SeedConfiguration") -> frozenset[int]:
    """Unsupported neutrality routes cannot hold progression or useful rewards."""
    if not configuration.option("settlement_reputation_logic"):
        return frozenset()
    return frozenset(id for id in SETTLEMENT_RULES if requirement(configuration, id) is None)


def required_reputation(
    configuration: "SeedConfiguration", checks: frozenset[int]
) -> dict[str, int]:
    """A faction's bases share one quota, never separate duplicated quotas."""
    return {
        rule.name: rule.copies
        for id in sorted(checks)
        if (rule := requirement(configuration, id)) is not None
    }
