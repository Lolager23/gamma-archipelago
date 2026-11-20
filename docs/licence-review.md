# Licence and redistribution review

This repository is private. No open-source licence has been selected for the
owned project code. The owner's licence decision is a public-release gate;
preparing private review artifacts does not select a licence or publish a release.
MIT is a proposed option compatible with the upstream project's MIT approach,
subject to Owen's choice. There is no public licence grant in this document.

| Component | Distribution in this project's packages |
|---|---|
| Owned Python/Lua, catalogue mappings, tests/docs | Owned source; owner licence decision remains pending |
| Anomaly/GAMMA/Haruka source, textures, sounds, binaries and saves | Not distributed; install independently through official instructions |
| Monolith/DXML | Existing installed APIs are called; no engine binaries or copied base scripts are included |
| Archipelago 0.6.8 | External pinned dependency, MIT; use upstream distribution and retain its notices |
| Archipelago coloured icon | Credited CC BY-NC 4.0 asset, copyright Krista Corkos and Christopher Wilson. Pinned PNG converted to DDS; attribution and separate noncommercial licence travel in the mod package. See `assets/archipelago/LICENSE.txt` and `mod/ARCHIPELAGO-ICON-LICENSE.txt`. |
| Python, websocket/YAML/Lua tooling and development dependencies | External pinned dependencies; no third-party binaries are bundled here |

References: [Archipelago licence](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/LICENSE),
[Monolith source](https://github.com/themrdemonized/xray-monolith), and the
[primary resource list](resources.md). Catalogue names, IDs and compatibility
mappings describe the installed baseline; they are not redistributed game files.
The deterministic package-content tests verify the owned-file boundary plus the
explicitly credited, byte-verified icon. This asset exception does not select a
licence for the project's owned code or change the public-release approval gate.

Before public release, choose and commit the owned-code licence, review the
actual final archives and dependencies' notices, complete engine acceptance and
obtain explicit publication approval. This review does not claim legal clearance
for distributing third-party game assets or imply affiliation with their owners.
