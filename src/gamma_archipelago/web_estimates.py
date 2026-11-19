"""Transparent planning heuristics, deliberately separate from generation logic."""

import math
from collections.abc import Mapping

from .configuration import GOALS, SeedConfiguration

ASSUMPTIONS = {
    "pace_percent": (100, 50, 200),
    "map_minutes": (25, 5, 90),
    "task_minutes": (20, 5, 90),
    "artefact_minutes": (25, 5, 90),
    "kills_per_hour": (12, 2, 120),
    "session_hours": (2, 1, 12),
    "multiworld_wait_minutes": (0, 0, 600),
}
GOAL_HOURS = (3, 8, 18, 30, 50, 30)


def estimate_playtime(
    configuration: SeedConfiguration,
    counts: Mapping[str, int],
    assumptions: Mapping[str, object],
) -> dict[str, object]:
    if set(assumptions) - ASSUMPTIONS.keys():
        raise ValueError("Unknown playtime assumption")
    settings = {}
    for name, (default, minimum, maximum) in ASSUMPTIONS.items():
        value = assumptions.get(name, default)
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValueError(f"{name} must be an integer from {minimum} to {maximum}")
        settings[name] = value
    route = counts.get("checks_maps", 0) * settings["map_minutes"] / 60
    tasks = counts.get("checks_story_milestones", 0) + counts.get("checks_quest_types", 0)
    if "checks_side_task_milestones" in configuration.checks:
        tasks = max(tasks, max(configuration.side_task_milestones))
    task_hours = tasks * settings["task_minutes"] / 60
    artefacts = counts.get("checks_artefacts", 0) * settings["artefact_minutes"] / 60
    kills = (
        max(configuration.kill_milestones)
        if "checks_kill_milestones" in configuration.checks
        else 0
    )
    combat = max(kills, counts.get("checks_mutant_first_kills", 0) * 3) / settings["kills_per_hour"]
    rank = 60 if "checks_rank_milestones" in configuration.checks else 0
    activity = max(task_hours, artefacts, combat, rank)
    locks = sum(mode == 2 for _, mode in configuration.gear) * 0.5
    base = GOAL_HOURS[GOALS.index(configuration.goal)]
    pace = settings["pace_percent"] / 100
    wait = settings["multiworld_wait_minutes"] / 60
    goal = (max(base, route * 0.5) + locks) * pace + wait
    completion = max(goal, (max(base, activity) + route + locks) * pace + wait)
    return {
        "goal_hours": [round(goal * 0.6, 1), round(goal * 1.6, 1)],
        "completion_hours": [round(completion * 0.6, 1), round(completion * 1.6, 1)],
        "sessions": [
            math.ceil(goal * 0.6 / settings["session_hours"]),
            math.ceil(goal * 1.6 / settings["session_hours"]),
        ],
        "breakdown_hours": {
            "goal_baseline": base,
            "map_travel": round(route, 1),
            "tasks": round(task_hours, 1),
            "artefact_hunt": round(artefacts, 1),
            "combat": round(combat, 1),
            "rank_floor": rank,
            "equipment_locks": locks,
        },
        "assumptions": settings,
        "confidence": "Uncalibrated heuristic; not measured playtime or a guarantee.",
        "method": (
            "Goal baseline plus equipment-lock allowance; completion uses the longest "
            "overlapping activity plus travel. Pace and extra multiworld waiting apply "
            "to both. Bounds are 60–160% scenarios, not statistical confidence intervals. "
            "Rank uses a provisional 60-hour floor; rare spawns, deaths and other players "
            "can extend a run beyond this range. Highest totals are counted once."
        ),
    }
