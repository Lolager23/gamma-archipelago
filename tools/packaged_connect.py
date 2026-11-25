"""Interactive connection setup for an explicitly selected player installation."""

import argparse
import getpass
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from gamma_archipelago.installation import (  # noqa: E402
    Installation,
    enroll,
    inspect_installation,
    require_enrolled,
)
from gamma_archipelago.paths import require_isolated_root, require_safe_child  # noqa: E402


def document(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        data = stream.read(65537)
    if len(data) > 65536:
        raise ValueError("Local settings exceed 64 KiB")
    result = json.loads(data.decode("utf-8-sig"))
    if not isinstance(result, dict):
        raise ValueError("Local settings must be a JSON object")
    return result


def processes() -> list[dict[str, Any]]:
    query = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -match 'python|Anomaly|xrEngine' } | "
        "Select-Object Name,ExecutablePath,CommandLine | ConvertTo-Json -Compress"
    )
    raw = subprocess.check_output(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", query], text=True
    )
    rows = json.loads(raw) if raw.strip() else []
    return [rows] if isinstance(rows, dict) else rows


def ensure_stopped(rows: list[dict[str, Any]], installation: Installation | None = None) -> None:
    if any(
        any(
            token in (row.get("CommandLine") or "").lower()
            for token in ("gammaarchipelagoclient.py", "run_client.py")
        )
        for row in rows
    ):
        raise ValueError("Close the existing GAMMA companion before configuring or connecting")
    if installation is not None and any(
        str(row.get("Name", "")).lower().startswith(("anomaly", "xrengine"))
        and (
            not row.get("ExecutablePath")
            or Path(row["ExecutablePath"]).is_relative_to(installation.game_root)
        )
        for row in rows
    ):
        raise ValueError("Close the selected game before configuring its AP installation")


def selected_installation(
    settings: Path, configure: bool, rows: list[dict[str, Any]]
) -> Installation:
    directory = require_isolated_root(settings.parent, settings.parent)
    path = require_safe_child(directory, "installation.json")
    if path.exists() and not configure:
        saved = document(path)
        installation = inspect_installation(
            Path(saved["game_root"]), appdata_root=Path(saved["appdata_root"])
        )
        require_enrolled(installation)
        return installation
    selected = Path(
        input("Anomaly folder (fsgame.ltx), or its GAMMA/MO2 folder: ").strip().strip('"')
    )
    try:
        installation = inspect_installation(selected)
    except ValueError as error:
        if "alias" not in str(error) and "appdata" not in str(error):
            raise
        print(str(error))
        appdata = Path(input("Active appdata folder from fsgame.ltx: ").strip().strip('"'))
        installation = inspect_installation(selected, appdata_root=appdata)
    ensure_stopped(rows, installation)
    print(f"Game: {installation.game_root}\nAppdata: {installation.appdata_root}")
    print("Use an AP-enabled MO2 profile and retain your save/profile backup.")
    if input("Type ENABLE to enroll this installation for Archipelago: ").strip() != "ENABLE":
        raise ValueError("Cancelled; installation was not changed")
    enroll(installation)
    path.write_text(
        json.dumps(
            {
                "game_root": str(installation.game_root),
                "appdata_root": str(installation.appdata_root),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return installation


def connect(
    settings: Path, *, slot: str | None = None, server: str | None = None, configure: bool = False
) -> None:
    data = document(settings)
    port = data.get("port", 38281)
    name = slot or data.get("slot")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Port must be an integer from 1 to 65535")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_ -]{1,16}", name):
        raise ValueError("Use the exact AP slot name, 1-16 letters/numbers/spaces/_/-")
    rows = processes()
    ensure_stopped(rows)
    installation = selected_installation(settings, configure, rows)
    if configure:
        print("Installation configured. Run your player Connect launcher next.")
        return
    address = (
        server
        or data.get("server")
        or input("AP host IP or hostname, optionally with port: ").strip()
    )
    if (
        not isinstance(address, str)
        or not address
        or len(address) > 256
        or any(c.isspace() for c in address)
        or "/" in address
    ):
        raise ValueError("Enter an AP host/IP and optional port")
    if ":" not in address:
        address += f":{port}"
    password = data.get("password") or getpass.getpass("AP room password (ask the host): ")
    if not isinstance(password, str) or not password or len(password) > 256:
        raise ValueError("A valid room password is required")
    print(f"Connecting {name} to {address}. Keep this window open.", flush=True)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "GammaArchipelagoClient.py"),
            "--nogui",
            "--name",
            name,
            "--connect",
            address,
            "--password",
            password,
            "--game-root",
            str(installation.game_root),
            "--appdata-root",
            str(installation.appdata_root),
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings", required=True, type=Path)
    parser.add_argument("--slot")
    parser.add_argument("--server")
    parser.add_argument("--configure", action="store_true")
    arguments = parser.parse_args()
    try:
        connect(
            arguments.settings.absolute(),
            slot=arguments.slot,
            server=arguments.server,
            configure=arguments.configure,
        )
    except subprocess.CalledProcessError as error:
        print(f"Companion stopped with exit code {error.returncode}", file=sys.stderr)
        raise SystemExit(1) from error
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(
            f"Connection stopped: {error}. Use Configure Game.cmd to select another installation.",
            file=sys.stderr,
        )
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
