# Build, test and deploy GAMMA Archipelago

## Current candidate

The 30-step candidate now implements expanded checks/rewards, options, permissions
and alternate goals. Start with the [implementation index](implementation-status.md)
and [preset matrix](configuration-and-balance.md). Owen performs engine acceptance
after each merge; do not launch/load the game automatically. Always use the
isolated development MO2 launcher for actual playtests.

For baseline script failures, use the dated
[GAMMA compatibility investigation](gamma-compatibility-investigation.md) and
`tools/inspect_probe_sources.py`. Candidate presence and source compilation do not
establish the engine's loaded winner or in-game compatibility.

Normal development uses [affected-area verification](testing-policy.md). The full
suite, including the 10,000-seed preset matrix and real server passes, runs only
for full releases or explicit release preparation. Test cases and regression
coverage continue to grow; game snapshots in server tests remain synthetic.

## Original pilot scope (historical)

The pilot has three finite checks: first arrival in Cordon, Garbage and Rostok.
Its shuffled pool contains a basic toolkit, medkit and bandage. Visiting all three
regions reports the pilot goal. It proves the integration boundary; it does not
yet replace GAMMA's progression or remove the ordinary sources of those items.
The AP world's reachability model deliberately has no item gates at this stage.

The existing multiplayer installation stays separate. Testing uses a fresh
single-player save in the development installation. Multiplayer support remains
an exploratory branch with its own installation and acceptance criteria.

## Local tooling

Python 3.12, Git and a C-backed LuaJIT runtime from the pinned Lupa wheel are used.
On this machine, the Python environment, upstream checkout and copied AP runtime
are under `D:/GAMMAAPTools`. Run commands from this source repository:

```powershell
$python = 'D:/GAMMAAPTools/python-env/Scripts/python.exe'
& $python -m pip install -e '.[dev]' -r requirements-ap.txt
& $python tools/verify.py
```

For another machine, create a virtual environment outside the game folders,
clone upstream tag `0.6.8` and provide explicit tooling paths:

```text
python tools/verify.py --ap-source <upstream-checkout> --ap-root <separate-runtime>
```

The bootstrap checks the upstream commit before copying its core and APQuest
reference world. It never edits the upstream checkout. Its minimal runtime avoids
installing dependencies for every unrelated AP game. `requirements-ap.txt` pins
the required subset; automatic upstream dependency updates are disabled here.

Normal verification selects the affected components and gates coverage for changed
owned runtime modules. Review the emitted `artifacts/verification-scope.json`.
For a stacked PR, pass `--base` with its actual parent branch/commit; use `--plan`
to inspect the selection. Static checks stay cheap and repository-wide.

Use `python tools/verify.py --full` for full release verification. It retains the
entire suite, all-module coverage, packaging/archive checks and complete seed
counts. Real generator/server tests run untraced in a second pass because this
Python/YAML tracing combination can produce invalid tags. Full releases require
both passes. Lua still measures executable lines and decision outcomes, not branch
coverage. Neither mode launches the game.

## Packages and deployment

GitHub runs affected verification on Windows/Linux for PRs and pushes to main.
Feature pushes do not duplicate PR jobs. Published GitHub releases run the full
suite; select `full` in the manual workflow for release preparation. Reports and
experimental packages are retained when produced; affected documentation/tooling
runs need not build unrelated deployment archives. Workflow permissions stay
read-only. Check the current PR head and its recorded scope before reporting CI.

If hosted billing blocks all job steps, the existing temporary repo-scoped runner
fallback remains available through `GAMMA_AP_SELF_HOSTED=true`. It changes job
placement only; the selected affected/full command and matrix are unchanged.
Use reviewed private code, remove registrations/credentials afterward and restore
the variable. Do not install permanent services or change billing. Billing failures
remain a separate owner action and must not be marked passed.

`python tools/build.py` writes deterministic `dist/gamma.apworld`,
`dist/gamma-archipelago-mo2.zip` and `dist/SHA256SUMS`. Only owned code and data are
packaged. The Lua and AP world catalogue copies are generated from
`src/gamma_archipelago/catalog.json`; edit that source rather than either copy.

The separately packaged `dist/gamma-archipelago-probes.zip` contains only the
opt-in diagnostic add-on. See [callback probes](callback-probes.md) for deployment,
source inventory, logs and the remaining in-game acceptance. It is not part of
the normal pilot package.

Wait for the official GAMMA installer to finish before deployment. Create the
`Archipelago DEV` MO2 profile as a copy of the fresh development default. The
installed game plugin reports that profile-local saves are unsupported: isolation
comes from the separate `D:/AnomalyAP/appdata`, not the MO2 checkbox. Use the
documented dev launch entry/configuration and a disposable single-player save.
The following command copies the add-on
only to `D:/GAMMAAP/mods/GAMMA Archipelago DEV`:

```powershell
& $python tools/deploy_mod.py
```

Enable that add-on only in the development profile. Confirm MO2 points to
`D:/AnomalyAP`, then launch through that MO2 instance. Keep the add-on disabled
for a baseline GAMMA smoke test. Deployment and the client reject alternate roots
and linked destinations; source and installed files are separate copies.

For the companion client:

```powershell
& $python tools/run_client.py --name GammaPilot --connect localhost:38281
```

Generate and host using the isolated upstream runtime:

```powershell
& $python tools/run_ap.py generate --player_files_path examples --outputpath D:/GAMMAAPTools/seeds --seed 20261118
& $python tools/run_ap.py host --host 127.0.0.1 --port 38281 D:/GAMMAAPTools/seeds/<generated-archive>.zip
```

Use the archive actually produced by generation. Hosting binds to loopback for
this local pilot. Player-facing launchers are a later delivery. Do not install
this experimental world into the shared AP installation.

## In-game acceptance still required

1. Verify the official install completed, all launch paths and profile isolation.
2. Start a fresh baseline save without the add-on, save/load and inspect its path.
3. Enable the add-on, connect a pilot slot and observe its startup log.
4. Visit each pilot region and confirm exactly three server checks and the goal.
5. Confirm the three received rewards are real inventory objects with valid sections.
6. Save/load, reconnect, disconnect during a check and load an older test save.
7. Attempt the wrong seed with that test save and verify refusal without delivery.
8. Disable the add-on and verify baseline operation; compare protected roots again.

Record versions, result and evidence in the verification record. Mock engine tests
do not satisfy these steps. Never load an existing multiplayer save for testing.

## Known pilot limits

Receipt state is saved with the game. Loading an older save replays receipts not
present there, including consumables. Item creation and saving cannot be made one
transaction through these callbacks; crash-proof exactly-once delivery is not
claimed. The recovery branch must choose and verify the final policy.

Partial outgoing files are rejected and retried on the next poll. Client incoming
snapshots use an atomic replacement. The supported session must stay in the same
seed and slot until the companion client restarts; saved mismatches are refused.
There is no progression balancing, status UI or normal item-source suppression yet.
