# Execution plan

## Outcome

Deliver a playable, documented GAMMA Archipelago randomiser with deterministic
generation, understandable progression, safe reconnect/save behaviour and a
repeatable release process. Develop and test it without altering the established
multiplayer installation. This is a staged project, not a commitment that every
proposed feature is technically possible.

The 18 November expansion request is specified in the
[expanded checklist](expansion-plan.md). Its stages 0–7 and the revised
[branch roadmap](branch-roadmap.md) are the current detailed implementation
sequence. The stages below describe the original project lifecycle and retain
its baseline, reliability and release gates. They do not reduce the newly
requested feature scope to the original three-check pilot.

## Stage 0: preserve and establish the baseline

Back up the full existing Anomaly `appdata`, MO2 profiles, `overwrite` and launch
configuration. Verify copied files by SHA-256. Record an inventory of both original
installation trees. Extract verified official Anomaly/GAMMA archives into the two
new drive-root folders, initialise Anomaly, run the official GAMMA installer and
verify the final mod count and game launch. Audit paths and reparse points, then
confirm that the original trees and save backup are unchanged.

Create the personal Git repository, standards, roadmap and CI. Keep game assets
and local evidence outside Git. Pin a tested Anomaly/GAMMA/AP baseline.

Exit: verified backup, isolated installation, source remote and initial PR.

## Stage 1: initial forays

Inspect upstream callbacks and current GAMMA overrides. Probe update, save/load,
level name, item creation, task completion and stash identity using a separate
diagnostic add-on. Identify which scripts win MO2 conflicts. Record observations
from the actual development build; community examples are leads, not proof.

Build a three-location pilot world and an upstream CommonClient adapter. Prove
one in-game check reaches a real local AP server and a received toolkit appears
in inventory. Verify the mod can be disabled without affecting the normal game.

Exit: reproducible vertical slice with live-server and in-game evidence.

## Stage 2: reliable session and save handling

Test wrong seed, wrong slot, bad files, partial writes, network failure, duplicate
packets, item gaps, manual save/load and old-save rollback. Separate checks and
permanent unlocks from consumables. Define recovery semantics before adding more
reward sources. Add a clear connection/status display and bounded logs.

Exit: regression suite covers the failure matrix and players can recover a session
without silently losing progress or receiving uncontrolled duplicates.

## Stage 3: a complete MVP

Implement the agreed finite checks and first progression pool from the
randomisation plan. Start with one faction, starting region and goal. Replace
normal sources of shuffled progression items, prove game-side gates agree with
generator rules, and keep survival supplies obtainable. Run many deterministic
seeds and a mixed-game multiworld. Complete at least two fresh playthroughs.

Exit: the MVP checklist is satisfied with no unresolved progression blockers.

## Stage 4: broaden and investigate

Implement the requested independent check/reward categories and five goal choices
through the expanded checklist's small branches. Map/quest access and stash,
reputation and skill rewards are requested work with explicit feasibility gates.
Research additional equipment licences, transition shuffling, traps, DeathLink
and xrRazom interaction as separate spikes.
Each spike has a question, time boundary, evidence and keep/drop decision. Features
that break saves or create excessive logic assumptions remain optional or are cut.

Exit: supported features are explicit, and exploratory ideas have recorded results.

## Stage 5: harden and finish

Freeze IDs and schemas. Audit compatibility, performance, install/uninstall,
accessibility of messages and error recovery. Test release packages on a clean
MO2 instance. Collect independent playtesting, balance long waits and verify
multiworld completion. Finish player and maintainer documentation, licences,
known issues, migration policy, checksums and tagged release automation.

Exit: release acceptance in `randomisation-plan.md` is met. Unsupported multiplayer
combinations and optional features are stated plainly.

## Evidence and estimation

Track each branch with acceptance tests, observed results and unresolved risks.
Use `not run`, `passed`, `failed` and `blocked` rather than ambiguous tick marks.
Estimate later stages after the vertical slice and first complete seed. Update the
plan when evidence changes it; do not preserve a bad design merely to follow a list.
