"""Maximum distinct opportunities under finite per-region encounter budgets."""

from functools import lru_cache


@lru_cache(maxsize=256)
def capacity(sources: tuple[tuple[str, ...], ...], regions: frozenset[str], starting: str) -> int:
    """Match each supported type once to five starting or two additional slots.

    Reassignment is essential: greedy counting can spend a unique source's only
    region on a common type. A maximum matching stays monotonic as routes open.
    """
    held: dict[tuple[str, int], int] = {}

    def assign(source: int, seen: set[tuple[str, int]]) -> bool:
        for region in sources[source]:
            if region not in regions:
                continue
            for position in range(5 if region == starting else 2):
                slot = region, position
                if slot in seen:
                    continue
                seen.add(slot)
                if slot not in held or assign(held[slot], seen):
                    held[slot] = source
                    return True
        return False

    return sum(assign(index, set()) for index in range(len(sources)))
