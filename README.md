# GAMMA Archipelago

Private **1.0.0rc1 candidate** for S.T.A.L.K.E.R. Anomaly with G.A.M.M.A.
The thirty core increments and local generator have been individually reviewed
and merged. The [merge audit](docs/merge-review-record.md) records fixes and checks.
Engine acceptance
belongs to Owen after each merge; this is not an accepted or publicly released v1.

| Feature | Implemented scope |
|---|---|
| Checks | 14 categories: 33 maps, 18 settlements, mutants/factions, artefacts, quests, story, equipment, kill/task totals and rank |
| Rewards | 7 categories: white/orange stashes, quest keys, goodwill, Haruka skills, zone keys and starting-equipment permissions |
| Starts | Normal, absent or AP-locked gear; supply percentages and No Starting Weapons |
| Goals | Calibrated psi protection, Brain Scorcher, Meet Strelok, Living Legend, all five labs, and the development three-region tour |
| PDA/MCM | Named transfers, no-PDA queues, toolkit test and optional previewed unlock travel |
| Recovery | Seed/slot binding, ordered receipts, durable checks, notice recovery and malformed-save refusal |

See the [implementation/PR index](docs/implementation-status.md),
[presets](docs/configuration-and-balance.md), and
[remaining engine acceptance](docs/multiworld-acceptance.md).
The full preset has 257 network checks. Local progression events are separate.

## Seed workbench

The [local generator web app](docs/generator-web-app.md) provides preset/category
controls, exact check and reward catalogues, adjustable playtime estimates, player
YAML downloads and real seed ZIP generation. Run `python tools/run_generator_web.py`
after preparing its separate runtime as documented, then open
`http://127.0.0.1:38290`. It does not launch the game or deploy the mod.

## Development and acceptance

The normal multiplayer installations `D:/Anomaly` and `D:/GAMMA` are protected.
The isolated pair is `D:/AnomalyAP` and `D:/GAMMAAP`; the desktop **GAMMA AP DEV**
shortcut opens that folder. **Launch through its Mod Organizer**, so enabled mods
load. Verification tools never launch the game.

After merging a step, close the game, follow the full appdata/profile backup
procedure, and deploy copies from that exact source revision:

```text
python tools/deploy_mod.py --component pilot
```

Follow the [development guide](docs/development-guide.md) and
[environment/restore policy](docs/development-environment.md). Keep world, client
and add-on revisions together. The [portable companion guide](docs/portable-client.md)
covers packaged installation. Source bootstrap creates a loose development world;
do not install a second archived copy into that same runtime.

## Verification and candidate packaging

Python 3.12 and Archipelago 0.6.8 are the tested tooling baseline:

```text
python tools/verify.py --ap-source <pinned-upstream-checkout> --ap-root <separate-runtime>
```

The verifier runs lint, formatting, typing, Python/Lua regressions, independent
coverage gates, 6,000 preset seeds, category/goal combinations, reproducible
packages, archive loading and ten real-server cases. Server game snapshots are
synthetic; these tests do not replace a GAMMA playthrough.

From a clean committed checkout:

```text
python tools/prepare_release.py
```

This creates a local candidate, source/file manifest and checksums. It never
merges, tags or publishes. See [v1 preparation](docs/version-one-release.md) for
remaining acceptance, review and owner licence decisions.

## Documents

- [Agent instructions](AGENTS.md), [coding standard](docs/coding-standard.md), [Git workflow](docs/git-workflow.md), [architecture](docs/architecture.md).
- [Execution plan](docs/execution-plan.md), [expanded checklist](docs/expansion-plan.md), [branch roadmap](docs/branch-roadmap.md), [randomisation goals](docs/randomisation-plan.md).
- [Primary resources](docs/resources.md), [verification record](docs/verification-record.md), [callback probes](docs/callback-probes.md), [hardening](docs/release-hardening.md).
- [Change log](CHANGELOG.md), [licence review](docs/licence-review.md), [notice](NOTICE.md).

Game files, assets, credentials and personal saves are not distributed. Install
Anomaly/GAMMA through official instructions. No affiliation with their owners or
Archipelago is implied. In-world multiplayer and exploratory stretch goals remain
separate future work.
