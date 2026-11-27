# Step 11: task types, side jobs and story milestones

Stack base: artefact PR #14. Three independent options add thirteen normalized
quest types (28052501–28052513), fifty-three story milestones (28052601–28052653)
and configured side-task totals. A side threshold's stable ID is 28120000 plus
its count; the finite selected list uses the same 1–20 thresholds and 1–10,000
count bounds as kill milestones. Only selected thresholds become seed locations.

Quest types are fetch, delivery, recovery, hunting, bounty, rescue, defence,
research, investigation, assault, donation, territory and vehicle destruction.
The catalogue maps actual status/target/title functors explicitly. Monster assault
parameters distinguish hunting from stalker assaults. Unrecognized templates can
still count as successfully completed nonstory side jobs, but do not invent a
quest-type classification. Story tasks are excluded from side totals and ordinary
quest-type checks, with explicit exceptions for successful native recovery and
faction-payment jobs. Native payments using `drx_sl_money_task_status` or `drx_sl_money_task_target` award Donation
(28052511) even though GAMMA marks them `storyline=true`. These payments stay out
of side-task totals. Donation means completing the faction-change fee task, such
as Sidorovich's **Burning Bridges**, rather than spending money at a trader or
merely accepting a task. Known main-trilogy story IDs retain their own checks and
never use this exception. The frozen main-trilogy roster covers Living Legend,
Mortal Sin and Operation Afterglow, grouping 83 faction variants into 53 shared milestones.
Other storylines are not silently classified as main-trilogy progress.

The installed Monolith `callbacks_gameobject.script` publishes
`actor_on_task_callback(task, state, manager, id)` before calling the ordinary task
manager. That provides the current task record before cleanup. Credit uses the
actual engine `task.completed` event, independently of reward collection. Accepted,
failed, cancelled and forced-failed states cannot count. No task-manager or binder
function is replaced by this add-on. The installed Fair Autocomplete wrapper was
also inspected: it delegates to the previous callback chain.

Repeatable job instances use the template ID and all seven fields of the saved
`inited_time` (including milliseconds). The source sets this time when granting
a task and restores it on load. Repeated completion events for that instance do
not increment totals; a later instance of the same template can. Missing/invalid
times produce a visible error instead of a template-only guess. Two separate
instances with the same template and identical engine timestamp would be treated
as duplicates; that engine-resolution boundary is not claimed to be an independent
global task UUID. Counters and seen instances are copied with the save and stop
growing at the largest configured threshold. Old saves migrate missing fields.

Story observations are retained independently of optional story checks for later
goal support. Story checks require story mode. Task categories refuse to run if
the installed Monolith hook is absent; late-loaded hooks can register on a later
poll without launching the game again. The current goal remains the three-map tour.
Global activity locations still assume ordinary task/story access; key prerequisites
and supported-start restrictions must be tightened in the gate/goal branches.

The full verifier passes 409 covered tests plus two real AP server cases, with
100% measured owned Python lines/branches and Lua executable lines. Tests cover
all mapped functors and story aliases, repeated templates, duplicate callbacks,
save copies/rollback, saturation, failure/cancellation, invalid timestamps,
missing/late hooks, story mode and exact standalone category generation/manifests.
Lua branch coverage is not measured. Actual completion timing, timestamp resolution
and installed task-mod interactions are **not run**, reserved for the user's
post-merge acceptance. No game launch, deployment or protected-root modification.

## GAMMA recovery and Flea Market defence

Recovery includes successful stash-document/quest-item retrieval using
`drx_sl_quest_item_task_status` / `drx_sl_quest_item_task_target` (for example
`simulation_task_46` in the active Dynamic Tasks Balance `tm_dynamic.ltx`),
`nta_stash_task_status_functor` / `nta_stash_task_target_functor` from New Tasks,
and the existing corpse and DRX retrieval functors. Generic fetch jobs remain a
separate check. Native DRX recovery jobs marked `storyline=true` can award Recovery
but never side-task totals; recognized main-trilogy IDs retain precedence.

Petrenko's **Hold the Ground** uses `hold_the_ground_task_status_functor` and
`hold_the_ground_task_target_functor`, now mapped to Defence. The active New Tasks
`tasks_hold_the_ground.script` identifies the Flea Market smart terrain and its
bandit waves. Credit is still the engine's successful task completion callback;
merely defending an area without completing a native task does not create a
check. Failed, abandoned, active and disabled checks cannot award either category.

Published IDs, configuration and save formats are unchanged. Existing completed
jobs are not reconstructed from absent task records; requested manual releases
recover the current run. These corrections require an updated game add-on for
future observations; no live deployment is part of this PR.

## Investigation opportunities

The active `simulation_task_52` Lost Signal task chooses Darkscape, Truck Cemetery,
Meadow, Zaton, Jupiter or Jupiter Outskirts, not Garbage. Tasks QoL removes the
northern destinations before both native psi emitters are disabled. AP placement
and the PDA require a reachable supported target region, the ordinary PDA
permission and Utilities permission when restricted (the RF receiver's native
`D_CUSTOM` / `i_device` classification). Access to a northern region also follows
the world's normal zone/quest rules. This describes a possible job, not a promise
that an accepted random job selected an unlocked map. The check remains
`reliable=false`, so generation excludes progression and useful rewards from it.
The receiver must still be acquired in game and the actual native task completed.
This changes future generation and the tracker projection, not the existing
server's pre-generated placements or its saved completion history.
