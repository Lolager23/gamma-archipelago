"""The development root is an explicit allowlist, not a path inferred from a running game."""

import os
from pathlib import Path

DEFAULT_GAME_ROOT = Path("D:/AnomalyAP")
DEFAULT_MO2_ROOT = Path("D:/GAMMAAP")


def require_isolated_root(path: Path, allowed_root: Path) -> Path:
    requested = Path(os.path.abspath(path))
    allowed = Path(os.path.abspath(allowed_root))
    if os.path.normcase(str(requested)) != os.path.normcase(str(allowed)):
        raise ValueError(f"Only the isolated development root is allowed: {allowed}")
    for candidate in (requested, *requested.parents):
        if candidate.is_symlink() or candidate.is_junction():
            raise ValueError(
                f"Filesystem links are not allowed in the development path: {candidate}"
            )
    if requested.resolve() != requested:
        raise ValueError("Development root resolves outside its explicit location")
    return requested


def require_safe_child(root: Path, relative: str) -> Path:
    child = root / relative
    if not child.is_relative_to(root) or not child.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path escapes the development root")
    candidate = child
    while candidate != root:
        if candidate.is_symlink() or candidate.is_junction():
            raise ValueError(f"Linked runtime paths are forbidden: {candidate}")
        candidate = candidate.parent
    if child.is_file() and child.stat().st_nlink > 1:
        raise ValueError("Runtime files must not be hardlinked")
    return child
