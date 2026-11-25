"""Select an AP installation with Windows' native folder picker; no Tk dependency."""

import argparse
import ctypes
import importlib
import json
import os
import sys
from ctypes import wintypes
from pathlib import Path
from types import ModuleType
from typing import Protocol


class Dialogs(Protocol):
    def folder(self, title: str) -> Path | None: ...
    def confirm(self, message: str) -> bool: ...
    def information(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...


class BrowseInfo(ctypes.Structure):
    _fields_ = [
        ("owner", wintypes.HWND),
        ("root", ctypes.c_void_p),
        ("display", wintypes.LPWSTR),
        ("title", wintypes.LPCWSTR),
        ("flags", wintypes.UINT),
        ("callback", ctypes.c_void_p),
        ("parameter", wintypes.LPARAM),
        ("image", ctypes.c_int),
    ]


class WindowsDialogs:
    def __init__(self) -> None:
        self.shell = ctypes.WinDLL("shell32", use_last_error=True)
        self.ole = ctypes.WinDLL("ole32", use_last_error=True)
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.shell.SHBrowseForFolderW.argtypes = [ctypes.POINTER(BrowseInfo)]
        self.shell.SHBrowseForFolderW.restype = ctypes.c_void_p
        self.shell.SHGetPathFromIDListEx.argtypes = [
            ctypes.c_void_p,
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        self.shell.SHGetPathFromIDListEx.restype = wintypes.BOOL
        self.ole.CoInitialize.argtypes = [ctypes.c_void_p]
        self.ole.CoInitialize.restype = ctypes.c_long
        self.ole.CoTaskMemFree.argtypes = [ctypes.c_void_p]
        self.ole.CoTaskMemFree.restype = None
        self.ole.CoUninitialize.argtypes = []
        self.ole.CoUninitialize.restype = None
        self.user.MessageBoxW.argtypes = [
            wintypes.HWND,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.UINT,
        ]
        self.user.MessageBoxW.restype = ctypes.c_int

    def folder(self, title: str) -> Path | None:
        initialized = self.ole.CoInitialize(None)
        if initialized not in (0, 1):
            raise OSError("Windows could not initialize the folder picker")
        item = None
        try:
            display = ctypes.create_unicode_buffer(32768)
            info = BrowseInfo(
                None, None, ctypes.cast(display, wintypes.LPWSTR), title, 0x51, None, 0, 0
            )
            item = self.shell.SHBrowseForFolderW(ctypes.byref(info))
            if not item:
                return None
            path = ctypes.create_unicode_buffer(32768)
            if not self.shell.SHGetPathFromIDListEx(item, path, len(path), 0):
                raise ValueError("Select a local filesystem folder")
            return Path(path.value)
        finally:
            if item:
                self.ole.CoTaskMemFree(item)
            self.ole.CoUninitialize()

    def confirm(self, message: str) -> bool:
        # Yes/No, question icon, default No; opening a picker is not consent to enroll.
        return self.user.MessageBoxW(None, message, "Configure Archipelago Game", 0x40124) == 6

    def information(self, message: str) -> None:
        self.user.MessageBoxW(None, message, "Archipelago Game Configured", 0x40040)

    def error(self, message: str) -> None:
        self.user.MessageBoxW(None, message, "Archipelago Configuration", 0x40010)


def configure(root: Path, dialogs: Dialogs, connector: ModuleType) -> bool:
    directory = connector.require_isolated_root(root, root)
    settings = connector.require_safe_child(directory, "installation.json")
    connector.ensure_stopped(connector.processes())
    while True:
        selected = dialogs.folder(
            "Select the Anomaly folder with fsgame.ltx, or its GAMMA/MO2 folder"
        )
        if selected is None:
            return False
        try:
            try:
                installation = connector.inspect_installation(selected)
            except ValueError as error:
                if "alias" not in str(error) and "appdata" not in str(error):
                    raise
                custom = dialogs.folder("Select the active appdata folder specified by fsgame.ltx")
                if custom is None:
                    return False
                installation = connector.inspect_installation(selected, appdata_root=custom)
            connector.ensure_stopped(connector.processes(), installation)
        except (OSError, ValueError) as error:
            dialogs.error(str(error))
            continue
        if not dialogs.confirm(
            f"Enable Archipelago for this installation?\n\nGame:\n{installation.game_root}\n\n"
            f"Appdata:\n{installation.appdata_root}\n\n"
            "Keep your save/profile backup and use an AP-enabled MO2 profile."
        ):
            return False
        connector.enroll(installation)
        settings.write_text(
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
        dialogs.information(
            "Game folder saved. Run Connect Mini.cmd (or your assigned player launcher)."
        )
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings-root", type=Path)
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit("The native folder picker requires Windows")
    root = args.settings_root or Path(__file__).resolve().parent
    if (
        not (root / "runtime/GammaArchipelagoConnect.py").is_file()
        and (root / "GammaArchipelagoConnect.py").is_file()
    ):
        root = root.parent
    dialogs = WindowsDialogs()
    try:
        if not (root / "runtime/GammaArchipelagoConnect.py").is_file():
            raise ValueError(
                "Place Configure Game.py beside connection.json and apply the path hotfix first"
            )
        sys.path.insert(0, str(root / "runtime"))
        connector = importlib.import_module("GammaArchipelagoConnect")
        configure(root.absolute(), dialogs, connector)
    except (OSError, ValueError, ImportError, KeyError, TypeError) as error:
        dialogs.error(str(error))
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
