"""Prepare a private, unaccepted candidate archive; never tag, merge or publish."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from bootstrap_ap import AP_COMMIT
from build import ROOT, require_safe_child

PACKAGES = (
    "gamma.apworld",
    "gamma-archipelago-mo2.zip",
    "gamma-archipelago-probes.zip",
    "gamma-archipelago-client.zip",
    "SHA256SUMS",
)


def require_clean_source() -> None:
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    if status.strip():
        raise SystemExit("Commit or preserve source changes before preparing a traceable candidate")


def prepare() -> Path:
    require_clean_source()
    subprocess.run([sys.executable, str(ROOT / "tools/build.py")], cwd=ROOT, check=True)
    require_clean_source()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = project["project"]["version"]
    if not isinstance(version, str) or not re.fullmatch(r"[0-9A-Za-z.]+", version):
        raise SystemExit("Candidate version must be a filename-safe project version")
    payloads = {name: require_safe_child(ROOT, "dist/" + name).read_bytes() for name in PACKAGES}
    for name in ("README.md", "NOTICE.md", "CHANGELOG.md"):
        payloads[name] = require_safe_child(ROOT, name).read_text(encoding="utf-8").encode("utf-8")
    for folder, suffix in (("docs", ".md"), ("presets", ".yaml")):
        directory = require_safe_child(ROOT, folder)
        for path in sorted(directory.glob("*" + suffix)):
            safe = require_safe_child(ROOT, path.relative_to(ROOT).as_posix())
            payloads[path.relative_to(ROOT).as_posix()] = safe.read_text(encoding="utf-8").encode(
                "utf-8"
            )
    manifest = {
        "version": version,
        "status": "unaccepted_private_candidate",
        "source_commit": revision,
        "archipelago_commit": AP_COMMIT,
        "python": "3.12",
        "engine_acceptance": "not_run",
        "publication_approved": False,
        "owned_code_licence": "owner_decision_pending",
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            for name, data in sorted(payloads.items())
        },
    }
    payloads["release-manifest.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    output = require_safe_child(ROOT, f"dist/gamma-archipelago-{version}.zip")
    temporary = require_safe_child(ROOT, f"dist/gamma-archipelago-{version}.tmp")
    with ZipFile(temporary, "w", compression=ZIP_STORED) as archive:
        for name, data in sorted(payloads.items()):
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system, info.external_attr = 3, 0o644 << 16
            archive.writestr(info, data)
    os.replace(temporary, output)
    checksum = require_safe_child(ROOT, f"dist/gamma-archipelago-{version}.zip.sha256")
    checksum.write_text(
        f"{hashlib.sha256(output.read_bytes()).hexdigest()}  {output.name}\n", encoding="ascii"
    )
    return output


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(prepare())
