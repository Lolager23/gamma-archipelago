# Step 33: configurable distinct discoveries

Merge-review correction: saved distinct observations must belong to an enabled,
non-excluded type under the saved configuration. A regression reproduced accepted
excluded/disabled observations that could inflate quota counts; those saves are
now refused before observations are copied or new checks advance. Empty older
discovery state still migrates normally. No published ID or save schema changed.

Stacks on scouting PR #41. Each existing discovery category remains independently
toggleable. Newly generated worlds and planner presets default to `first_n_distinct`
for mutant kills, faction kills and artefacts. Named checks remain available through
`per_type`. Repeated kills or pickups of the same type do not advance generic checks.
`mutant_discovery_count`, `faction_discovery_count` and `artefact_discovery_count`
select N; zero means every qualifying type. The respective catalogue rosters have
25, 13 and 66 types. A quota of 15 gives fixed checks for discoveries 1 through 15
in any encounter order. It never requires one particular hidden selection of 15.
Repeated types and aliases cannot advance it. Quota mode replaces per-type checks.

This changes generation defaults only. Legacy configuration snapshots that omit the
mode keep their original per-type interpretation and digest; explicitly saved
options remain authoritative. Do not replace those legacy parser defaults with the
new-generation defaults. Existing archives, saves and active sessions are unchanged.

`discovery_exclusions` is a set/list of canonical tokens from the catalogue, for
example `faction:stalker`, `mutant:dog`, `artefact:af_atom`. Excluded types cannot
produce checks or advance quotas. Counts above the remaining roster and empty
check pools fail generation with an explanation; required rewards are never
silently dropped. Rarity is not inferred from ALife spawn probability.

`optional_check_policy` applies to the seven fragile shop/standing checks:
`exclude_progression` (default), `omit`, or `allow_progression`. The first retains
checks but forbids required progression there; the last explicitly accepts NPC
and allegiance risks. Standard AP `exclude_locations` can additionally prevent
progression at particular checks. This does not guarantee a mortal NPC survives.

The world, companion manifest, native enabled-check projection and web preview
use the same catalogue selection. New quota IDs occupy an unused range; all
published IDs retain their meaning. The build generates source/token/quota tables.
Side-task previews have an explicit upper bound so these IDs cannot leak into
that preview category.

## Save and configuration boundaries

Distinct observations are saved as a bounded set of canonical original source
IDs, separate from quota check IDs. Save validation rejects unknown IDs, non-true
values and missing session identity. Old saves without the optional set migrate
to empty; default per-type checks retain their completion and provenance. The
server's checks remain monotonic after older-save rollback, while observations
in the restored save may need to be encountered again. Fixed check IDs and server
deduplication prevent additional rewards from rediscovering them.

New zero/empty defaults are omitted from configuration digests. Non-default
settings require a newly generated seed and matching world/client/add-on bundle.
The data-only configuration snapshot adds canonical `exclude|group:type` records;
the parser validates tokens, duplicates, total record bounds and quota capacity.
No receipt format or save schema number changes.

## Acceptance

Automated tests cover first-15-of-25 discovery ordering, repeat/alias handling,
all three rosters, exclusions, impossible quotas, optional policies, manifest and
preview parity, source callbacks, save/load, malformed state and legacy defaults.
Native verification is **not run**, reserved for Owen: species/faction attribution,
contained artefact aliases, death callbacks, excluded targets, quota saturation,
PDA refresh and ordinary/older-save reload. No deployment, game launch or installed
game changes are included.

The complete verifier passed: 883 covered tests, 35 untraced generator/server
tests and five Node tests (923 total), including 60 filled full-progression seeds
using all three quota groups and service policies. Owned Python runtime modules
reached 100% measured line/branch coverage; Lua reached 100% measured executable
lines. Lua branch coverage is not measured.


## Progression-free final discoveries

`mutant_filler_tail` (0–25) and `artefact_filler_tail` (0–66) protect the final X
configured generic discoveries. For example, mutant quota 15 with tail 5 gives
checks for the first 15 distinct species; checks 11–15 accept filler only. The
same rule works for artefacts. It does not select specific rare types. Repeats
and aliases still cannot advance a distinct count. Per-type mode remains available.

A nonzero tail requires that category and generic mode, and cannot exceed the
selected quota after exclusions. All protected checks remain present and completable.
The APWorld marks them EXCLUDED before fill; useful and progression rewards are
both forbidden there. The shared budget reserves required permissions against the
remaining reliable checks and fails impossible configurations. Native observation
IDs and published check meanings are unchanged. Zero defaults preserve old digests
and configuration wire bytes. New settings require a new seed.
