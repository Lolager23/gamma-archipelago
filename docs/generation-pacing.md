# Generation budgets, openings and previews

Step 39 builds on the convenience-reward increment. The world owns placements;
the shared core calculates counts and validates settings. Neither the browser nor
the game chooses rewards. Native acceptance and measured playtime calibration
remain **not run**.

## Independent options

| Option | Values; default preserves earlier seeds |
|---|---|
| `opening_policy` | 0 legacy/challenge; 1 protected local Cordon opening |
| `access_pacing` | 0 random reachable frontier; 1 reachable hubs first |
| `combat_logic` | 0 any weapon permission; 1 firearms; 2 firearms, outfit and helmet |
| `grind_profile` | 0 custom thresholds; 1 short; 2 standard; 3 extended |
| `generation_preview` | 0 off; 1 actual-seed summary; 2 summary plus placement spoilers |

Combat assumptions require the corresponding permissions only when that starting
gear is AP locked. They do not measure native weapon condition, ammunition,
armour quality or a player's fighting ability. The PDA uses the same permission
requirements when explaining blocked combat checks. Access pacing changes the
local zone-key route; it does not promise early high-end equipment.

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
Cordon map check for the first route key; settlement checks provide the other
opening slots. If space remains, a normal Medkit or Bandage is reserved too.
Optional supplies respect non-local selections and each location's item rule;
the reservation tries an allowed fallback or skips supplies when neither fits.

Insufficient reliable checks, non-local opening items or conflicting plando fail
generation. Enable settlements, relax locked gear, precollect required permissions
or explicitly choose legacy/challenge mode. Random mutant encounters and rare
artefacts never count as opening guarantees. Native weather, hostile patrols and
survival supplies remain normal GAMMA concerns and need Owen's playtesting.

The new `short`, `standard` and `extended` presets use protected openings. Existing
six presets retain legacy settings. Hubs-first route priority is Garbage, Rostok,
Yantar, Agroprom and Wild Territory when reachable. Precollected zone keys expand
the reachable frontier without duplicating the removed keys.
Remaining route keys must be local: conflicting `non_local_items` settings fail
explicitly before placement. Already precollected keys need no placement and do
not create that conflict.

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
