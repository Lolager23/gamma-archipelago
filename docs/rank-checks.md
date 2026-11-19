# Step 13: Stalker Rank milestones

Stack base: equipment PR #16. `checks_rank_milestones` adds eight checks,
28052801–28052808, from Novice through Legend. The active GAMMA script interval
lower bounds are 0, 3999, 5999, 9999, 15999, 23999, 34999 and 49999. These are
the actual `ranks.get_rank_interval` lower bounds from the active `rating` table,
not rounded assumptions about base Anomaly or UI display boundaries. Starting
at Novice counts as reaching its initial milestone.

The adapter compares all eight installed intervals with the seed's frozen roster
before querying `actor:character_rank()`. Missing APIs, different thresholds,
exceptions and invalid rank values refuse this check configuration before reward
creation. This avoids silently changing location semantics when a different rank
mod is installed. The rank API and the active Economy/Improved Ranks configuration
were inspected; no rank, reputation or faction value is modified by the add-on.

Valid ranks update a saved high-water mark. Jumps award every reached threshold;
rank loss and ordinary reload do not remove or repeat checks. Older saves without
the field start at -1 and observe their current rank. Server-confirmed location
recovery remains independent of this local high-water value. Disabled categories
and legacy pilot seeds never query the rank API.

The complete verifier passes 430 covered tests plus two real AP server cases,
with 100% measured owned Python lines/branches and Lua executable lines. Tests
cover every boundary just below/at the threshold, rank loss, save/load, baseline
mismatch, invalid values, API exceptions and standalone eight-location generation.
Lua branch coverage is not measured. Live UI boundary alignment and installed
rank-mod behaviour are **not run**, reserved for the user's post-merge acceptance.
No game launch, deployment or protected-root modification was performed.
