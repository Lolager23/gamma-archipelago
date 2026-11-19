# Game callback probes

## Purpose and boundary

Branch `codex/game-callback-probes` supplies a separate diagnostic MO2 add-on,
source inventory and log summary. It investigates engine behaviour before new
Archipelago checks depend on it. It does not send checks, process AP receipts,
change task results, alter stash contents or automatically spawn items.

Owned source is under `probes/gamedata/scripts`. `tools/build.py` produces
`dist/gamma-archipelago-probes.zip` separately from the pilot add-on. The probe
namespace is `gamma_ap_probe_`; its only saved value is the diagnostic marker in
`gamma_ap_probe_v1`, separate from the pilot's receipt namespace.

The add-on registers only when appdata resolves by the engine to
`D:/AnomalyAP/appdata`. Every callback and manual reward attempt rechecks that
root. Deployment uses the same Python path/link guards as the pilot. Do not run
deployment while the official installer is working, or test with multiplayer saves.

## Source findings, 18 November 2026

The following are source observations, not completed in-game acceptance:

| Probe | Inspected implementation | Finding to verify in-game |
|---|---|---|
| Startup | Anomaly `axr_main.script` | Scripts exposing `on_game_start` are discovered before their startup methods run |
| Update and level | `axr_main.script`, `bind_stalker.script` | Use the registered actor update hook and sample `level.name()` at 500 ms intervals |
| Save/load | `axr_main.script`, installed add-ons | Callbacks receive the shared save table; preserve other namespaces |
| Item take | Anomaly `bind_stalker_ext.script` | The script callback receives the item; it can fire before the actor is fully ready |
| Box take | `bind_stalker_ext.script`, GAMMA `treasure_manager.script` | Signature is `(box, item)`; a box event is not automatically a unique stash check |
| Artefact | Anomaly item/statistics scripts | `IsArtefact(item)` classifies the received object; this does not prove pickup provenance |
| Task state | Anomaly binder and task manager | Vanilla forwards the engine task callback to `task_manager.task_callback` |
| Extended task hook | Installed `callbacks_gameobject.script` | Monolith adds `actor_on_task_callback(task, state, manager, id)` before the original task callback runs |

The probe subscribes to the extended task hook only when the already-loaded
`callbacks_gameobject` module exposes its captured `task_callback`. It records
`task_hook: missing` otherwise. It never invents an empty callback or replaces a
task-manager/binder function. `completed`, `failed`, other state and the manager's
`cancelled_by_actor` flag are observations; repeatable-task reset and cancellation
semantics still need live measurement.

The official Anomaly scripts archive was unpacked for inspection under
`D:/GAMMAAPTools/anomaly-base`, using the supplied converter. Game source remains
outside Git. Reference hashes from this inspection:

| File | SHA-256 |
|---|---|
| Base `bind_stalker_ext.script` | `8717f80bb0ac8c4085398ded6a70074ce27311a7f993dcb3081af011e5f05153` |
| Base `task_manager.script` | `dc7131f946ca965503752ab356e3d4a3c801fdf0d7caa7971e917cb4611d0ebd` |
| Development loose `axr_main.script` | `f10a322d083a88c8a3c17e8289af98f512a77ac672b282bde3dd1548efe75753` |
| Development loose `callbacks_gameobject.script` | `71b9b2d3d1c8a50a7277c09b1a0d9f5668fc5ba1a0517e710cd3259c8be6958d` |

Upstream cross-check: [Monolith callback extension at the inspected commit](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/gamedata/scripts/callbacks_gameobject.script).
The installed file hash identifies the local reference; the current upstream
commit is not a claim that the installed engine uses that exact build.

## Find the winning source after installation

The saved profile stores highest-priority entries first. MO2 accepts the first
occurrence of a repeated mod entry, as documented by its
[profile loader](https://github.com/ModOrganizer2/modorganizer/blob/master/src/profile.cpp).
The inspected GAMMA profile repeats `G.A.M.M.A. Vehicles in Darkscape`; a regression
test ensures the inventory preserves first occurrence rather than rejecting the
official profile or silently changing its priority. Paths and invalid entries
are rejected before files are inspected.

```powershell
$python = 'D:/GAMMAAPTools/python-env/Scripts/python.exe'
& $python tools/inspect_probe_sources.py --profile 'Archipelago DEV'
```

This reads only the development profile and loose script candidates, recording
their hashes in overwrite, saved mod-list order and game loose files. During
installation the default profile can be inspected with `--profile 'G.A.M.M.A'`.
Any enabled-but-missing entries or changing profile need another inventory after
installation. Do not repair the installer-owned profile from this tool.

The provisional inventory found three enabled loose `treasure_manager.script`
candidates: `G.A.M.M.A. Rare Stashes Balance`, `62- Stash Overhaul No Loot -
Grokitach`, then `60- Stash Overhaul - Grokitach`. No runtime winner is asserted.
Archives, renamed/hidden files, unsaved MO2 settings and monkey patches require
additional inspection. In MO2's Data/Conflicts views confirm each file's origin,
then inspect loaded modules and record the result with the final mod-list hash.
Keep the machine-specific JSON inventory outside Git.

## Live run procedure

1. Confirm successful installer completion, expected game paths and an isolated
   baseline GAMMA launch. Copy the fresh profile to `Archipelago DEV`, enabling
   profile-specific saves and settings. Retain the baseline save and log.
2. Build and deploy only the diagnostic add-on:

   ```powershell
   & $python tools/build.py
   & $python tools/deploy_mod.py --component probes
   ```

   Enable `GAMMA Archipelago Callback Probes DEV` in that profile. Initially leave
   `GAMMA Archipelago DEV` disabled so probe observations have no AP reward traffic.
3. Start a fresh Loner/Cordon save. Confirm `started`, `task_hook` and `level`
   records. An absent log is `not run` or a failed probe, not evidence of no event.
4. Pick up ordinary loot and an artefact; transfer an item from a known static
   stash, a dynamic stash and a player-created box. Record the actual actions
   alongside object IDs/names, level and callback order. Repeat an item transfer
   and load an older save to check whether candidate identities remain stable.
5. Accept, complete, fail and cancel separate safe test jobs. Compare log records
   with PDA state and reward timing. Distinguish task requirements becoming
   satisfied from final turn-in and the original manager removing/resetting data.
6. Save twice, load each save and compare `save`/`load` marker records. An old save
   may correctly restore a lower marker. Verify other mod and pilot state survive.
7. On the expendable save, manually invoke the one-shot reward probe through the
   engine's supported debug console:

   ```text
   run_string gamma_ap_probe_game.try_reward()
   ```

   The command syntax is present in base Anomaly script examples but must be
   confirmed on the installed engine. The helper attempts only one `bandage`
   creation per probe startup, including a failed attempt. Observe the inventory,
   save/load and verify persistence. A `reward: created` log alone proves neither
   inventory ownership nor saved persistence. No attempt happens automatically.
8. For a pilot coexistence run, enable the pilot too, connect its matching AP slot
   and repeat a short save/load and delivery sequence. Compare server checks,
   receipt state and diagnostic observations; the probes must not send checks.
9. The optional `run_string gamma_ap_probe_game.stop()` unregisters only this
   add-on's callbacks. For removal, quit, disable the probe add-on in MO2 and
   restart. Load an expendable probe save, verify baseline operation and absence
   of new probe records. Do not infer removal from merely hiding log messages.
10. Re-audit protected installation and backup inventories after game testing.

## Log format and reporting

Records use the engine log, prefixed `GAMMA_AP_PROBE|1`, followed by sequence,
engine clock in milliseconds, event, level and three scalar values. Delimiters and
control characters are removed from values; fields are at most 96 characters.
There are at most 256 records per startup and no per-frame log spam. Start a new
short test session if the record cap is reached. Duplicate callbacks are retained
within that bound for investigation rather than hidden by deduplication.

```powershell
& $python tools/report_probes.py <development-engine-log>.log
```

The filename must be under `D:/AnomalyAP/appdata/logs`. The tool rejects directory
arguments and linked paths, reads without modifying the log and prints a summary.
It counts malformed probe lines without copying unrelated log text or personal
save filenames. Reports always say `acceptance: not assessed`; a human observation
and the appropriate engine evidence complete each acceptance check. Keep raw logs
and machine-specific reports outside Git.

## Evidence status

| Check | Required result | Current status |
|---|---|---|
| CB-01 | Add-on loads only in the isolated game; callback order recorded | not run in-game |
| CB-02 | First update, throttle and level changes match actual actions | not run in-game |
| CB-03 | Save/load marker survives and other namespaces remain intact | not run in-game |
| CB-04 | Item and artefact events distinguish observed actions/provenance | not run in-game |
| CB-05 | Static/dynamic/player box identities measured across reloads | not run in-game |
| CB-06 | Task acceptance, completion, failure and cancellation measured | not run in-game |
| CB-07 | Manual bandage appears, is owned and persists after reload | not run in-game |
| CB-08 | Pilot coexistence preserves checks and receipt state | not run in-game |
| CB-09 | Disable/restart restores baseline without new probe callbacks | not run in-game |
| CB-10 | Protected trees and backups remain unchanged after live tests | not run for this branch's live tests |

Automated tests exercise the real Lua probe modules under LuaJIT with mock engine
boundaries and test Python parsing/source-order logic. They verify separate package
contents and copied deployment into temporary folders. They do not run GAMMA or
complete the table above. The branch remains draft while live checks are pending.

The local verifier currently passes 140 covered tests and two real AP-server tests.
Owned Python runtime modules have 100% line and branch coverage; all five owned
non-generated Lua modules have 100% executable-line coverage. Lua branch coverage
is not measured. The local Windows runner also prints faulthandler stack traces
when tests deliberately raise and catch Lua errors; those assertions and the
overall process exit succeed. No tracing or failing check is disabled to suppress
that output. Hosted CI evidence belongs to the branch's PR and current head.
