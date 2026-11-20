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

The complete verifier includes a covered regression pass plus untraced runs for
6,000 preset seeds and ten actual server cases. Game snapshots in server tests
are synthetic. Local events do not consume network check slots.

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

Verification runs formatting, lint, strict typing of the framework-independent
core, generation, packaging, regression tests and independent per-module line and
branch coverage thresholds. World and CommonClient public interfaces are typed;
their runtime integration is tested against the actual pinned framework.
It also generates 1,000 deterministic pilot seeds, tests a mixed-game world,
loads the packaged `.apworld` through the upstream loader and runs two real
loopback websocket sessions: solo and mixed with APQuest.

The real generator/server tests run in a second, untraced pass. On the installed
Python 3.12.3 build, tracing upstream's C-backed YAML loader produces invalid
`None` tags. Both passes are required and fail the command on errors. Owned
world/client coverage comes from the preceding regression tests; no production
module is excluded. Lua uses executable-line tracing with JIT disabled and
decision-outcome tests; this is not a Lua branch-coverage measurement.

## Packages and deployment

The same verification job runs on Windows and Linux through
`.github/workflows/verify.yml`, on pushes and pull requests. It retains coverage
reports and experimental packages as run artifacts. The repository uses read-only
workflow permissions. Check both job results on the PR before declaring CI passed.

If GitHub refuses hosted jobs before any steps run because of account billing or
spending limits, the repository variable `GAMMA_AP_SELF_HOSTED=true` selects local
runners labelled `self-hosted,gamma-ap-windows-latest` and
`self-hosted,gamma-ap-ubuntu-latest`. This changes only job placement: the Windows
and Linux matrix, pinned actions/dependencies, complete verifier and retained
artifacts remain identical. The matrix names identify their targets; record the
actual local operating systems/Python versions rather than calling them hosted
images. With the variable absent or false, the standard hosted runners are used.

Use temporary repo-scoped runners under `D:/GAMMAAPTools`, only for reviewed code
in the private repository. Do not install a permanent service or change billing.
Remove registrations/credentials after the jobs finish and restore the variable
to its previous state. Account billing remains a separate owner action; failed
hosted runs must retain their original annotations rather than being marked passed.

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
