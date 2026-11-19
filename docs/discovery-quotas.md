# Step 33: configurable distinct discoveries

Stacks on scouting PR #41. Each existing discovery category remains independently
toggleable. Its mode is `per_type` (default, existing checks) or `first_n_distinct`.
`mutant_discovery_count`, `faction_discovery_count` and `artefact_discovery_count`
select N; zero means every qualifying type. The respective catalogue rosters have
25, 13 and 66 types. A quota of 15 gives fixed checks for discoveries 1 through 15
in any encounter order. It never requires one particular hidden selection of 15.
Repeated types and aliases cannot advance it. Quota mode replaces per-type checks.

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
