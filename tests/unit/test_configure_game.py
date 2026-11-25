import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from gamma_archipelago.installation import enroll, inspect_installation
from gamma_archipelago.paths import require_isolated_root, require_safe_child

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("configure_game", ROOT / "tools/configure_game.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Dialogs:
    def __init__(self, choices, consent=True):
        self.choices = iter(choices)
        self.consent = consent
        self.errors = []
        self.information_messages = []

    def folder(self, title):
        return next(self.choices)

    def confirm(self, message):
        return self.consent

    def information(self, message):
        self.information_messages.append(message)

    def error(self, message):
        self.errors.append(message)


def connector():
    return SimpleNamespace(
        require_isolated_root=require_isolated_root,
        require_safe_child=require_safe_child,
        inspect_installation=inspect_installation,
        enroll=enroll,
        processes=lambda: [],
        ensure_stopped=lambda *args: None,
    )


def game(tmp_path):
    root = tmp_path / "Game with spaces"
    root.mkdir()
    (root / "appdata").mkdir()
    (root / "fsgame.ltx").write_text("$app_data_root$=true|false|$fs_root$|appdata\\\n")
    return root


def test_folder_picker_selection_uses_the_shared_validator_and_saves_choice(tmp_path):
    selected = game(tmp_path)
    ui = Dialogs([selected])
    assert module.configure(tmp_path, ui, connector())
    assert str(selected).replace("\\", "\\\\") in (tmp_path / "installation.json").read_text()
    assert (selected / "appdata/archipelago/installation.txt").is_file()
    assert ui.information_messages and not ui.errors


def test_windows_picker_structure_accepts_the_output_buffer_without_opening_ui():
    import ctypes

    buffer = ctypes.create_unicode_buffer(32768)
    info = module.BrowseInfo(
        None, None, ctypes.cast(buffer, module.wintypes.LPWSTR), "Select folder", 0x51, None, 0, 0
    )
    assert info.title == "Select folder" and info.flags == 0x51


@pytest.mark.parametrize("cancel_picker", [True, False])
def test_cancel_picker_or_confirmation_never_enrolls(tmp_path, cancel_picker):
    selected = game(tmp_path)
    ui = Dialogs([None if cancel_picker else selected], consent=False)
    assert not module.configure(tmp_path, ui, connector())
    assert not (tmp_path / "installation.json").exists()
    assert not (selected / "appdata/archipelago").exists()


def test_bad_folder_explains_the_error_then_allows_a_new_selection(tmp_path):
    selected = game(tmp_path)
    ui = Dialogs([tmp_path, selected])
    assert module.configure(tmp_path, ui, connector())
    assert ui.errors


def test_custom_alias_opens_a_second_folder_picker(tmp_path):
    selected = game(tmp_path)
    (selected / "fsgame.ltx").write_text("$app_data_root$=true|false|$custom$|data")
    data = tmp_path / "Custom appdata"
    data.mkdir()
    assert module.configure(tmp_path, Dialogs([selected, data]), connector())
    assert (data / "archipelago/installation.txt").is_file()
    assert not (selected / "appdata/archipelago").exists()


def test_cancel_custom_appdata_picker_does_not_write(tmp_path):
    selected = game(tmp_path)
    (selected / "fsgame.ltx").write_text("$app_data_root$=true|false|$custom$|data")
    assert not module.configure(tmp_path, Dialogs([selected, None]), connector())
    assert not (tmp_path / "installation.json").exists()
