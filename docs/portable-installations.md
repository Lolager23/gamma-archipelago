# Player-selected Anomaly and GAMMA paths

On 25 November 2026 Owen requested generic player installation support after the
private playtest package rejected a friend's real game folder. The original
development safety rule had been carried into both the launcher and the native
adapter. Removing the launcher's folder check alone would still leave native
checks/rewards, notices and scouting pointed at an unsupported path.

## Player flow

Install 64-bit Python 3.12 with pip and the launcher. If `py -3.12 --version`
reports no runtime, `py -0p` lists the detected versions. A different installed
version is not the requested 3.12 interpreter. The official compatible Windows
installer is [Python 3.12.10 x64](https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe).

After preparing the private AP runtime and installing the MO2 add-on, close the
game and start the connection launcher. On first use it asks for either:

- The Anomaly folder containing `fsgame.ltx`.
- Its portable Mod Organizer folder containing `ModOrganizer.ini`; its `gamePath`
  must resolve to the actual Anomaly folder.

The helper resolves the usual `$app_data_root$` alias relative to the selected
game. Unsupported alias chains require an explicit active appdata directory;
they are not guessed. It shows both paths and asks the player to type `ENABLE`
before enrolling that installation. Keep appdata/profile/configuration backups
and use an AP-enabled MO2 profile. There is no need to move or rename the game.

The choice is saved in the launcher's local `installation.json`. It contains only
paths. Server, slot and room password remain separate connection settings. The
`--configure` option repeats installation selection without starting networking.
If a cached folder was moved, configure again. Do not relocate a running session's
bridge by copying just individual receipt files.

## Filesystem contract

The selected appdata directory's `archipelago/installation.txt` contains exactly
`GAMMA_AP_INSTALLATION|1` followed by a newline. It is static enrollment metadata,
not a command, session identity, item acknowledgement or additional save ledger.
The CLI requires enrollment before constructing a portable bridge. The game reads
its actual engine `$app_data_root$` and requires this marker outside the original
DEV root. An unregistered install does not deliver rewards or write game snapshots.

The Python helper rejects missing/non-absolute paths, drive roots, network/device
paths, unsupported aliases, oversized/malformed configuration, filesystem links,
hardlinked marker/bridge files and unrecognized existing markers. Supported local
drive paths include different drive letters and spaces. The Lua projection
normalizes engine `bin/..` aliases, rejects drive-relative/traversal/device paths,
and reads a bounded marker before enabling an alternate root. Native Windows game
acceptance remains manual; generic path normalization is not a portability claim
for Linux game builds, UNC installs or unsupported engine versions.

## Compatibility and isolation

Owen's `D:/Anomaly` and `D:/GAMMA` stay protected. Agents must not enroll them or
write to them. Owen's existing DEV client/default path continues to work without
new arguments, and its current installation, developer panel, seed and progress
are not changed by implementing this feature. Temporary test directories provide
the alternative installations used by automated tests.

The AP world definitions, item/check IDs, protocol versions and save schemas are
unchanged. Update the companion and add-on together for a portable player. An
existing player using the legacy DEV path remains network-compatible with that
player: the change selects a filesystem location, not a different item pool or
session. Never transplant a character between AP seeds to test this feature.

Verification must include arbitrary directories with spaces, MO2 game-path
resolution, explicit custom appdata, refused/unregistered roots, malformed and
oversized files, link/hardlink refusal, a generic native adapter mock, real archived
APWorld loading, and a real server/client transfer using the selected bridge.
