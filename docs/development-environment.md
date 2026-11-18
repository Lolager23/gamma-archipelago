# Development environment

## Protected normal game

The existing multiplayer game is `D:/Anomaly`, managed by `D:/GAMMA`. Both existing
profiles currently share the Anomaly appdata save directory. No development tools
may write to either root. The baseline inventory and backup manifest live outside
Git under `D:/GAMMAAPTools` and `D:/GAMMA-AP-Backups`.

Before installation, the complete `D:/Anomaly/appdata` tree was copied, along with
both MO2 profiles, `overwrite`, `ModOrganizer.ini`, `fsgame.ltx`, launcher settings
and command-line settings. All 859 files in the three copied trees were verified
against their source SHA-256. The dated backup is
`D:/GAMMA-AP-Backups/2026-11-18_174828`. Keep it private: it includes personal saves.

## New installation

Use **two separate drive-root folders**, `D:/AnomalyAP` and `D:/GAMMAAP`, following
the current GAMMA Discord installation guide. The source repository remains in the
user-selected workspace; game installations are outside OneDrive.

Anomaly 1.5.3 is extracted from the official full archive. Its SHA-256 is
`E564D9110E673EACFA5604B0837F6E6208EAE4CD46CD5682326ED59F931527AE`.

The current official GAMMA RC3 archive is 12,248,276,398 bytes with SHA-256
`00A554364EE6881F16D1080F75D92175E4B19FE372265ECA211DE7478FDCC037`.
The wiki checksum was stale; the downloaded file was matched to the current file
metadata in the MediaFire folder linked by the official Discord guide. That
provenance is retained in the private environment records.

Run vanilla Anomaly once to its main menu, then run the official GAMMA launcher's
First Install Initialization. Select only `D:/AnomalyAP` in MO2. Close MO2, run
Install / Update with the official defaults, and verify the completion message.
Use DX11 for the first GAMMA launch. Record the launcher/build and mod-definition
versions after installation, rather than assuming the old wiki's version number.

Do not copy the existing multiplayer game's patched `gamedata` or engine files.
Do not share downloads or mods using filesystem links. Existing archives may be
read as installation inputs; the installed files and writable caches are separate.
Check the resolved executable, working directory, appdata, mod, profile, overwrite
and updater paths before running anything. Existing desktop shortcuts must not be
overwritten; give development shortcuts an unmistakable `AP DEV` name.

## Development workflow

Deploy the repository's `mod` directory as a named MO2 add-on in the development
instance only. Keep a copied `Archipelago DEV` profile based on the freshly
installed default. Use a fresh test save. Runtime bridge data lives only at
`D:/AnomalyAP/appdata/archipelago`. The companion client must reject the original
game root even if it is passed accidentally.

Build tools and the pinned upstream AP checkout live under `D:/GAMMAAPTools`.
Neither the installed shared Archipelago instance nor another game's AP worlds
are changed. Run the client from the isolated Python environment.

Verification includes a post-install path scan, absence of crossover links, a
development save/settings write, and comparison of the original installation
inventory. Record an actual in-game result separately from command-line tests.

## Restore

Close Anomaly and MO2 before restoring. Copy the dated backup's Anomaly-appdata
tree back to the intended original appdata root only when a restore is explicitly
requested. Preserve the current state as another dated backup first. Restore MO2
profiles/configuration separately if required. Never merge development saves into
the normal multiplayer save directory.
