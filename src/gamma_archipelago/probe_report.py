"""Summarise diagnostic observations without treating them as game acceptance."""

import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

PREFIX = "GAMMA_AP_PROBE|"
EVENTS = frozenset(
    {
        "started",
        "stopped",
        "first_update",
        "level",
        "item",
        "artefact",
        "box",
        "task",
        "save",
        "load",
        "reward",
        "error",
        "task_hook",
    }
)
MAX_OBSERVATIONS = 10000


class ProbeFormatError(ValueError):
    """A diagnostic line is malformed or exceeds the report's bound."""


@dataclass(frozen=True)
class ProbeObservation:
    sequence: int
    clock_ms: int
    event: str
    level: str
    values: tuple[str, str, str]


def parse_line(line: str) -> ProbeObservation | None:
    start = line.find(PREFIX)
    if start < 0:
        return None
    fields = line[start:].rstrip("\r\n").split("|")
    if len(fields) != 9 or fields[1] != "1":
        raise ProbeFormatError("Unsupported or incomplete diagnostic line")
    if any(re.fullmatch(r"0|[1-9][0-9]{0,9}", value) is None for value in fields[2:4]):
        raise ProbeFormatError("Diagnostic counters must be canonical nonnegative integers")
    if not 1 <= int(fields[2]) <= 256 or fields[4] not in EVENTS:
        raise ProbeFormatError("Unsupported diagnostic event or sequence")
    if any(re.fullmatch(r"[A-Za-z0-9_.:/-]{1,96}", value) is None for value in fields[5:]):
        raise ProbeFormatError("Diagnostic fields contain invalid or oversized values")
    return ProbeObservation(
        int(fields[2]), int(fields[3]), fields[4], fields[5], (fields[6], fields[7], fields[8])
    )


def summarize(lines: Iterable[str]) -> dict[str, object]:
    counts: Counter[str] = Counter()
    levels: set[str] = set()
    malformed = 0
    total = 0
    for line in lines:
        if PREFIX not in line:
            continue
        total += 1
        if total > MAX_OBSERVATIONS:
            raise ProbeFormatError("Too many diagnostic observations; use a shorter log")
        try:
            observation = parse_line(line)
        except ProbeFormatError:
            malformed += 1
            continue
        assert observation is not None
        counts[observation.event] += 1
        if observation.level != "-":
            levels.add(observation.level)
    return {
        "schema_version": 1,
        "evidence": "diagnostic log observations; game acceptance requires corroboration",
        "counts": dict(sorted(counts.items())),
        "levels": sorted(levels),
        "malformed_lines": malformed,
        "acceptance": "not assessed",
    }
