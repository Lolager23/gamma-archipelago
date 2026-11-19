"""Optional actual-seed summaries; item placements require an explicit spoiler choice."""

import json
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from BaseClasses import CollectionState

from gamma_archipelago.paths import require_safe_child

if TYPE_CHECKING:
    from . import GammaWorld


def write_preview(world: "GammaWorld", output_directory: str) -> None:
    mode = world.configuration.option("generation_preview")
    if not mode:
        return
    locations = sorted(
        (row for row in world.multiworld.get_locations(world.player) if row.address is not None),
        key=lambda row: row.address,
    )
    if any(row.item is None for row in locations):
        raise ValueError("Complete item fill before writing an actual-seed preview")
    initial = CollectionState(world.multiworld)
    initial.sweep_for_advancements(
        locations=[row for row in world.multiworld.get_locations() if row.address is None]
    )
    report = {
        "schema_version": 1,
        "kind": "actual_generated_seed",
        "seed": world.multiworld.seed_name,
        "player": world.player,
        "configuration_key": world.configuration.digest,
        "configuration": world.configuration.to_values(),
        "budget": world.pool_budget.report(),
        "opening_guarantees": world.opening_placements,
        "initial_reachable_checks": [row.name for row in locations if row.can_reach(initial)],
        "placed_classifications": dict(Counter(row.item.classification.name for row in locations)),
        "native_verification": "not run",
        "playtime": "Uncalibrated; reachability is not measured travel or ALife waiting.",
    }
    if mode == 2:
        report["spoiler_placements"] = [
            {
                "location": row.name,
                "location_id": row.address,
                "item": row.item.name,
                "recipient": row.item.player,
                "item_id": row.item.code,
            }
            for row in locations
        ]
    root = Path(output_directory)
    filename = world.multiworld.get_out_file_name_base(world.player) + "_gamma_preview.json"
    require_safe_child(root, filename).write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
