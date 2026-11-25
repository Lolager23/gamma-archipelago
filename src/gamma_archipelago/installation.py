"""Explicit enrollment of a player's installation, independent of the DEV defaults."""

import os
import re
from dataclasses import dataclass
from pathlib import Path

from .paths import require_isolated_root, require_safe_child

MARKER_NAME = "installation.txt"
MARKER = "GAMMA_AP_INSTALLATION|1\n"
MAX_CONFIG_BYTES = 65536


@dataclass(frozen=True)
class Installation:
    game_root: Path
    appdata_root: Path


def _directory(path: Path) -> Path:
    if not path.is_absolute():
        raise ValueError("Select an absolute installation path")
    root = require_isolated_root(path, path)
    if os.name == "nt" and root.drive.startswith("\\"):
        raise ValueError("Select a local drive directory, not a network or device path")
    if not root.is_dir() or root == Path(root.anchor):
        raise ValueError("Select an existing installation directory, not a drive root")
    return root


def _text(path: Path) -> str:
    with path.open("rb") as stream:
        data = stream.read(MAX_CONFIG_BYTES + 1)
    if len(data) > MAX_CONFIG_BYTES:
        raise ValueError("Installation configuration exceeds 64 KiB")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("Installation configuration must be UTF-8 text") from error


def game_directory(selected: Path) -> Path:
    """Accept the Anomaly directory or a portable MO2 directory naming its game."""
    root = _directory(selected)
    config = require_safe_child(root, "fsgame.ltx")
    if config.is_file():
        return root
    mo2 = require_safe_child(root, "ModOrganizer.ini")
    if not mo2.is_file():
        raise ValueError("Select Anomaly's folder containing fsgame.ltx, or its MO2 folder")
    matches = re.findall(r"^gamePath=(.+)$", _text(mo2), re.MULTILINE)
    if len(matches) != 1:
        raise ValueError("Cannot resolve MO2 gamePath; select the Anomaly folder directly")
    value = matches[0].strip()
    if value.startswith("@ByteArray(") and value.endswith(")"):
        value = value[11:-1]
    game = _directory(Path(value.replace("\\\\", "/").replace("\\", "/")))
    if not require_safe_child(game, "fsgame.ltx").is_file():
        raise ValueError("MO2 gamePath does not contain fsgame.ltx")
    return game


def appdata_directory(game: Path, override: Path | None = None) -> Path:
    """Resolve the installed alias, failing explicitly for unsupported alias chains."""
    if override is not None:
        return _directory(override)
    matches = re.findall(
        r"^\s*\$app_data_root\$\s*=([^\r\n;]+)",
        _text(require_safe_child(game, "fsgame.ltx")),
        re.MULTILINE | re.IGNORECASE,
    )
    if len(matches) != 1:
        raise ValueError(
            "Cannot resolve $app_data_root$; explicitly select the active appdata folder"
        )
    fields = [part.strip() for part in matches[0].split("|")]
    if len(fields) != 4 or fields[2].lower() != "$fs_root$":
        raise ValueError("Unsupported appdata alias; explicitly select its active directory")
    relative = fields[3].replace("\\", "/")
    if not relative or Path(relative).is_absolute() or re.match(r"^[A-Za-z]:", relative):
        raise ValueError("Appdata suffix must be relative to $fs_root$")
    # Collapse ordinary bin/.. forms before checking every resolved path for links.
    candidate = Path(os.path.abspath(game / relative))
    require_safe_child(game, relative)  # Refuse links/escapes instead of resolving through them.
    return _directory(candidate)


def inspect_installation(
    selected: Path, *, appdata_root: Path | None = None, protected: tuple[Path, ...] = ()
) -> Installation:
    game = game_directory(selected)
    appdata = appdata_directory(game, appdata_root)
    for candidate in (game, appdata):
        if any(candidate == root or candidate.is_relative_to(root) for root in protected):
            raise ValueError("The selected installation belongs to a protected game")
    return Installation(game, appdata)


def enroll(installation: Installation) -> None:
    """The setup UI calls this only after the player explicitly chooses the install."""
    root = _directory(installation.appdata_root)
    directory = require_safe_child(root, "archipelago")
    directory.mkdir(exist_ok=True)
    marker = require_safe_child(directory, MARKER_NAME)
    if marker.exists():
        if not _marker_matches(marker):
            raise ValueError("Unrecognized installation marker; no existing state was replaced")
        return
    marker.write_text(MARKER, encoding="ascii", newline="\n")


def _marker_matches(path: Path) -> bool:
    with path.open("rb") as stream:
        return stream.read(len(MARKER) + 1) == MARKER.encode("ascii")


def require_enrolled(installation: Installation) -> None:
    marker = require_safe_child(installation.appdata_root, "archipelago/" + MARKER_NAME)
    if not marker.is_file() or not _marker_matches(marker):
        raise ValueError("Configure and confirm this installation in the AP launcher first")
