"""Inspect loose script candidates without claiming the live engine's winning source."""

import hashlib
from collections.abc import Iterable
from pathlib import Path

from .paths import require_safe_child

WATCHED_SCRIPTS = (
    "axr_main.script",
    "callbacks_gameobject.script",
    "bind_stalker_ext.script",
    "task_manager.script",
    "treasure_manager.script",
    "news_manager.script",
    "haru_skills.script",
    "ranks.script",
    "xr_statistic.script",
    "lc_extra_transitions.script",
    "actor_effects.script",
    "ui_pda.script",
    "character_creation.script",
)


def enabled_mods(lines: Iterable[str]) -> tuple[str, ...]:
    """Preserve highest-first order and MO2's first-occurrence duplicate policy."""
    result = []
    seen = set()
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name = line[1:]
        if (
            line[0] not in "+-*"
            or not name
            or name in {".", ".."}
            or any(character in name for character in "/\\:")
        ):
            raise ValueError("Invalid modlist entry; inspect the profile before using its order")
        if name.casefold() in seen:
            continue
        seen.add(name.casefold())
        if line[0] != "-":
            result.append(name)
    return tuple(result)


def inspect_sources(game_root: Path, mo2_root: Path, profile: str) -> dict[str, object]:
    if not profile or profile in {".", ".."} or any(character in profile for character in "/\\:"):
        raise ValueError("Profile must be a single folder name")
    modlist = require_safe_child(mo2_root, f"profiles/{profile}/modlist.txt")
    content = modlist.read_bytes()
    mods = enabled_mods(content.decode("utf-8-sig").splitlines())
    sources = [(mo2_root, "overwrite", "overwrite")]
    sources.extend((mo2_root, f"mods/{name}", name) for name in mods)
    sources.append((game_root, ".", "game loose files"))
    files = {}
    for name in WATCHED_SCRIPTS:
        candidates = []
        for root, relative, label in sources:
            path = require_safe_child(root, f"{relative}/gamedata/scripts/{name}")
            if path.is_file():
                candidates.append(
                    {"source": label, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                )
        files[name] = {"ordered_candidates": candidates, "runtime_winner": "not verified"}
    if modlist.read_bytes() != content:
        raise ValueError("Profile changed during inspection; retry after installation finishes")
    return {
        "schema_version": 1,
        "profile": profile,
        "modlist_sha256": hashlib.sha256(content).hexdigest(),
        "enabled_mods": len(mods),
        "missing_enabled_mods": [
            name for name in mods if not require_safe_child(mo2_root, f"mods/{name}").is_dir()
        ],
        "scope": "saved profile and loose files only; archives/runtime patches unresolved",
        "files": files,
    }
