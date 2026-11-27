# Step 11: task types, side jobs and story milestones

The original Step 11 stack built on artefact PR #14. New generation uses twelve
normalized quest types (28052501–28052512), with Vehicle (28052513) retained only
for existing seeds. Three independent options select quest types, fifty-three story milestones (28052601–28052653)
and configured side-task totals. A side threshold's stable ID is 28120000 plus
its count; the finite selected list uses the same 1–20 thresholds and 1–10,000
count bounds as kill milestones. Only selected thresholds become seed locations.

Quest types are fetch, delivery, recovery, hunting, bounty, rescue, defence,
research, investigation, assault, donation and territory. Vehicle destruction is
reserved for the legacy roster.
The catalogue maps actual status/target/title functors explicitly. Monster assault
parameters distinguish hunting from stalker assaults. Unrecognized templates can
still count as successfully completed nonstory side jobs, but do not invent a
quest-type classification. Story tasks are excluded from side totals and ordinary
quest-type checks. The frozen main-trilogy roster covers Living Legend, Mortal Sin
and Operation Afterglow, grouping 83 faction variants into 53 shared milestones.
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

## Vehicle check retirement

New worlds have twelve quest-type checks: Vehicle Destruction (28052513) is
retired from generation, previews and the generator category count. Its published
ID, name and native functor mappings remain reserved and readable for existing
seeds. An internal `quest_type_roster` compatibility value is one in new
generation and zero when absent from an older seed. Zero is omitted from the
wire and digest, preserving existing session identities, confirmations, saved
checks and receipt histories. It is hidden from the normal generator controls.
Older clients need the matching updated bundle before connecting to new worlds.
The active session is not regenerated; requested manual releases complete the
old check without deleting or replacing its reward.
