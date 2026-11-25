"""Maximum distinct opportunities under finite per-region encounter budgets."""

import json
from functools import lru_cache
from importlib.resources import files

_RULES = json.loads(files(__package__).joinpath("catalog.json").read_text(encoding="utf-8"))[
    "mutant_diversity"
]


@lru_cache(maxsize=256)
def capacity(sources: tuple[tuple[str, ...], ...], regions: frozenset[str], starting: str) -> int:
    """Match distinct types to catalogue-owned starting and additional region slots.

    Reassignment is essential: greedy counting can spend a unique source's only
    region on a common type. A maximum matching stays monotonic as routes open.
    """
    held: dict[tuple[str, int], int] = {}

    def assign(source: int, seen: set[tuple[str, int]]) -> bool:
        for region in sources[source]:
            if region not in regions:
                continue
            slots = (
                _RULES["starting_region_overrides"].get(region, _RULES["starting_region_slots"])
                if region == starting
                else _RULES["additional_region_slots"]
            )
            for position in range(slots):
                slot = region, position
                if slot in seen:
                    continue
                seen.add(slot)
                if slot not in held or assign(held[slot], seen):
                    held[slot] = source
                    return True
        return False

    return sum(assign(index, set()) for index in range(len(sources)))
