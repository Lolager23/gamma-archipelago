# Generation budgets, openings and previews

## Actual progressive reward spacing

`progressive_sphere_pacing` constrains item placements, not just the step report.
Living Legend, Full Story, Full Labs, Standard and Extended enable it. Sparse
Pilot/Explorer/MVP/Restricted/Short presets keep it off because they can lack
enough gated checks for all copies. It is editable in the APWorld and workbench.

After normal AP fill, a bounded repair moves overlapping progressive equipment
or tool receipts into later reachable checks by swapping with non-progression
rewards. It preserves item counts, item rules, locality, fixed/planned placements,
all GAMMA check reachability, every player's goal and the three-step recipe
deadline. Zone keys and other progression rewards are not swap candidates. No
new artificial access rule is attached to a check.

Each recipient chain gets at most one receipt per network sphere with local
events settled, and at most one per actual upstream `get_spheres()` sphere.
Explicit starting inventory is exempt. Item-link groups count as shared recipients.
Fixed contradictions or insufficient depth fail with an actionable option error;
failed attempts restore the original placement and locks.

The pinned framework permits placement changes in `finalize_multiworld` after
upstream balancing, provided accessibility is preserved or increased. The hook
runs there and requires every previously reachable location in both models to
remain reachable, including other games' optional locations. It locks the resulting
progressive placements. `pre_output` only validates again, after all finalisers;
it never moves items. A later change that violates spacing rejects generation
rather than exporting an invalid seed. Some custom finaliser/plando combinations
can therefore require revised settings or disabling this constraint.

The displayed AP progression remains the paced activity model (including task,
kill and five-artefact batches). The separately labelled raw sphere report retains
ordinary AP activity reachability; both now respect the actual progressive-reward
placement constraint when enabled. Sphere/step counts are not measured playtime.

Step 39 builds on the convenience-reward increment. The world owns placements;
the shared core calculates counts and validates settings. Neither the browser nor
the game chooses rewards. Native acceptance and measured playtime calibration
remain **not run**.

## Independent options

| Option | Values; default preserves earlier seeds |
|---|---|
| `opening_policy` | 0 legacy/challenge; 1 protected local Cordon opening |
| `access_pacing` | 0 normal Archipelago fill; 1 request one early hub key |
| `combat_logic` | 0 any weapon permission; 1 firearms; 2 firearms, outfit and helmet |
| `grind_profile` | 0 custom thresholds; 1 short; 2 standard; 3 extended |
| `generation_preview` | 0 off; 1 actual-seed summary; 2 summary plus placement spoilers |

Combat assumptions require the corresponding permissions only when that starting
gear is AP locked. They do not measure native weapon condition, ammunition,
armour quality or a player's fighting ability. The PDA uses the same permission
requirements when explaining blocked combat checks. Hub pacing uses upstream
`early_items` without fixing a check or locality. It does not promise early high-end equipment.

Short thresholds are 5/15/30 kills and 1/3/6 tasks; standard thresholds are
10/25/50/100 kills and 5/10/20/40 tasks; extended thresholds are 25/75/150/250 kills
and 10/25/50/75 tasks. Custom lists remain editable when the profile is custom.
Switching profiles does not overwrite the browser's custom draft lists.

## Budget before fill

`pool_budget` counts enabled network checks, reliable placement capacity,
mandatory progression copies, precollected gifts, starting-from-pool depletion,
capped carry rewards and remaining filler slots before creating pool items.
Progressive Tools need three copies. Required permissions are never truncated.
AP's excluded locations accept filler only: they forbid useful items too.
All eight Stalker Rank checks are always excluded from progression placement,
including Novice, even when AP goodwill is enabled or legacy playability logic
is selected. They remain optional checks with ordinary filler rewards. Their
native triggers and AP-goodwill access proxy are unchanged. Existing archives
keep their original placements; this policy applies to newly generated worlds.

Standard AP `start_inventory` gifts reduce mandatory copies. The newly supported
`start_inventory_from_pool` precollects guaranteed permission/carry copies and
lets upstream remove those copies once, replacing their slots with filler.
Requests for random filler or more guaranteed copies than exist are refused
instead of silently using upstream's warning/fallback. Disabled, unknown,
malformed or over-limit starting inventories fail with an actionable error.
The combined starting/network receipt bound remains 4,000.

Plando and non-local constraints still undergo upstream fill validation. Protected
opening permissions must stay local and conflicts with reserved checks are
explicit failures. The preview is not a guarantee that every arbitrary common-AP
constraint combination will fill.

## Protected opening

A fresh **Loner in Cordon** is the supported baseline. Protected mode reserves
reliable Cordon map/settlement checks for an AP-locked PDA, a detector when artefact
checks need it, and firearms when the selected combat assumptions need them.
Already precollected permissions need no reservation. Zone-key seeds keep the
Cordon map check free for randomized access progression; settlement checks provide the other
opening slots. If space remains, a normal Medkit or Bandage is reserved too.
Optional supplies respect non-local selections and each location's item rule;
the reservation tries an allowed fallback or skips supplies when neither fits.

Insufficient reliable checks, non-local opening items or conflicting plando fail
generation. Enable settlements, relax locked gear, precollect required permissions
or explicitly choose legacy/challenge mode. Random mutant encounters and rare
artefacts never count as opening guarantees. Native weather, hostile patrols and
survival supplies remain normal GAMMA concerns and need Owen's playtesting.

The `short`, `standard` and `extended` presets use protected openings. Existing
six presets retain their settings. Hubs-first requests one remaining key from
Garbage, Rostok, Yantar, Agroprom and Wild Territory, in that preference order.
Upstream chooses an eligible early check and retains its normal fallback when
that request cannot be satisfied early. Precollected keys are skipped. The old
YAML name `random_frontier` remains an alias for value zero.

Expanded regional pools, including multiworlds, leave zone keys in normal AP fill.
Local/non-local item settings, priorities and exclusions apply normally. Only a
pool without a reliable non-map opening opportunity retains the exploration
anti-cycle fallback. Regional activities can now supply intermediate checks;
story-only checks behind the first area key cannot supply opening slack.
A fully locked activity opening requests one usable permission through upstream
`early_items`, without a fixed location or starting gift. Explicit early requests
and protected openings remain authoritative. Pinned AP fill failed sparse maps-only solo/multiworld
regression seeds without this exception. Fallback placements remain unlocked
and respect item rules; excluded route checks and conflicting sparse-route non-local
keys fail explicitly. This does not claim uniform sampling.

The existing map-check requirement and settlement requirement for exclusive psi
stash/key combinations remain until richer activity logic supports alternatives.
They provide reliable regional capacity, not forced key/check pairings in expanded
pools. Pool capacity, protected-opening validation and logical fill still apply.
A maps-only local pool necessarily awards its keys through map checks.

## Recipe opening

With `regional_progression` and `playability_logic` enabled, new seeds place every
enabled recipe permission within the first three **paced** steps. This includes
General, Medical, Ammunition and Artefacts. Starting gifts and upstream from-pool depletion are
respected; they do not create duplicate recipe rewards. Explicitly disabling either
setting retains ordinary challenge/legacy fill. The older all-zones activity
contract can lack enough opening capacity under fully locked starting gear.

After existing opening equipment and sparse key reservations, the world plans
recipes against a bounded partial-world calculation. That calculation uses the
same kill/task chains, five-artefact batches and one-tier progressive receipts as
the final report. It completes reachable unknown checks without assuming their
rewards, and collects only actual placed or planned items. Additional normal fill
can improve this conservative opening. All recipe reservations are validated
before committing any of them.

Candidates respect item rules, excluded checks and local/non-local item settings.
Non-local recipes may use another player's early checks; the opening record's
`finder` identifies that player's slot. Existing planned recipe placements are
preserved when they meet the deadline. Insufficient capacity or a late planned
recipe fails with an actionable error: add early checks, precollect permissions,
relax the conflicting constraint or disable playability logic. The generator does
not silently move a planned item or weaken its access requirements.

The deadline assumes all available checks are completed in each modelled step;
it does not guarantee real-time delivery from another player. No current archive,
running server, bridge or save is rewritten. Applying the placement change needs
a newly generated seed; previous analysis remains historical evidence.

## Previews and compatibility

The local workbench exposes tracker, hints, quotas/exclusions, supply choices and
pacing controls. Its settings preview shows the resolved thresholds, qualifying
rosters, opening permissions and budget. It has no placements or ALife knowledge.
Playtime estimates are explicitly uncalibrated scenarios.

After real fill, optional `*_gamma_preview.json` records seed/player, configuration,
budget, opening placements and initial logic-reachable checks. Summary mode omits
the full placement list; mode 2 explicitly adds spoilers. A report is refused
before all network checks have items. Reports are generated artifacts, not Git
source, and do not indicate native verification.

New scalar defaults are zero and omitted from legacy digests. Published item and
location IDs and the saved bridge schema are unchanged. Legacy slot schemas 1–3
retain their session identities. Non-default common AP constraints or precollected
items use **slot-data schema 4** with a canonical SHA-256 generation identity,
binding the session key to those constraints and starting items. This prevents
reusing a save under a changed starting inventory while keeping the same seed
name/team/slot. Schema 4 requires this matching companion; an older client refuses
it. Generate a fresh seed and keep world/client/add-on together for new options.

## Acceptance

Automated regressions cover opening conflicts/self-locks, missing spare supply
slots, gifted and depleted copies, precollected zone routes, common-option session
identity and spoiler boundaries. The full verifier additionally fills every preset
and independent pacing combinations, loads the APWorld archive and runs actual
solo/mixed-game AP sessions. The complete local verifier passed 979 covered,
49 untraced generator/server and six Node tests: 1,034 total, including 9,000
preset seeds. Owned Python modules reached 100% measured lines/branches and Lua
reached 100% measured executable lines; Lua branch coverage is not measured.
Browser checks exercised controls, exclusions, invalid configurations and recovery.
Current-head Windows/Linux results belong to the PR evidence.

Owen still needs to verify the opening in a fresh save, PDA blocked reasons,
native key/access enforcement, actual delivery effects and short/standard/extended
playtimes. No installed game, local developer panel or running AP session was
changed for this increment.

## Natural progression follow-up (21 November 2026)

Owen selected natural AP progression without imposed early/mid/late item tiers.
The active seed had all 32 zone keys on map-arrival checks because the old route
forced those pairings. The expanded-pool correction removes that reservation;
it never rewrites an existing archive, bridge identity, receipt or game save.

Use real access rules, progression classifications and ordinary AP fill.
Upstream progression balancing addresses relative progress in multiworlds; it is
not a guarantee of specific gear quality or hours played. Opening protection,
user plando/locality/exclusions and discovery filler tails remain explicit
exceptions. Do not remove essential requirements just to make checks look early.

The all-zones activity guard has been replaced by
[regional source and equipment requirements](regional-activity-logic.md).
Common early kills, artefacts and supported tasks can now hold zone keys. Distinct
quotas count supported reachable types after exclusions; uncertain sources and
quota excess are filler-only. No strict item tiers or category-placement quotas
are imposed. Native encounter availability and measured pacing remain unverified.

References checked against pinned AP 0.6.8 and current official documentation:
[World API](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/docs/world%20api.md),
[fill and early-item implementation](https://github.com/ArchipelagoMW/Archipelago/blob/54803be064fc7e80c4628777ed0b46a9390f255f/Fill.py),
[common balancing/accessibility options](https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/generic/docs/advanced_settings_en.md).
