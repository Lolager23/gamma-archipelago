# Expansion two: tracker, rewards and pacing

Requested 19 November 2026. This extends the original thirty-step plan. All rows
are proposed until their source and automated evidence are recorded. Engine
acceptance belongs to Owen; do not launch, load or deploy the game automatically.
The implementation was delivered as stacked draft PRs beginning at PDA
localization #38, with compatibility investigation #39 independent. Owen then
authorized sequential source review, fixes and merges; see the
[merge-validation record](expansion-two-merge-review.md). Native acceptance stays
with Owen, and public release remains a separate decision.

| Step | Branch | Contract | Native acceptance |
|---|---|---|---|
| 31 | `codex/pda-tracker` | Optional PDA AP tab; completed/available/blocked checks, reasons, regional filters and goal/progression summary. Read-only projection from the sole game-state owner. | Tab placement/aspect ratios, other tabs, refresh, no-PDA and load/reload |
| 32 | `codex/ap-scouting` | Optional hints/scouting, finite shop and faction-service checks, optional next side-task/faction reward previews; real LocationScouts metadata, recipient names and spoiler controls. | Trader identity, purchase/hand-in triggers, PDA interaction |
| 33 | `codex/discovery-quotas` | Per-type versus first-N-distinct mutant/faction/artefact checks; configurable exclusions; rare/missable check policy. Fixed published IDs, saved distinct observations. | Attribution, repeated kills/items, rare/faction exclusions, rollback |
| 34 | `codex/progressive-tools` | Optional progressive basic/advanced/expert tool permission with real repair/crafting enforcement and matching solver requirements. Native acquisition stays normal when off. | Tools, repair/crafting actions, ordinary-source bypass, receipt recovery |
| 35 | `codex/workshop-access` | Optional workshop/recipe permissions with explicit supported action/recipe groups and real engine guards. Refuse unsupported integrations with actionable errors. | Technician and self-crafting routes, recipes, compatibility |
| 36 | `codex/permission-supplies` | Optional one-time starter supplies attached to permissions; per-receipt action plans survive partial failure and normal save/load. No crash-proof exactly-once claim. | Partial spawn failure, retry, ordinary/older-save reload |
| 37 | `codex/supply-packages` | Independently selectable medical, maintenance, ammunition and expedition packages; bounded quantities and useful filler weights. | Valid sections, quantities, relevance, economy |
| 38 | `codex/convenience-rewards` | Optional bounded convenience rewards using supported APIs; explicit claims and safety conditions. No automatic hazardous travel or uncontrolled price changes. | Weight/service/travel effects, caps, rollback and native hazards |
| 39 | `codex/generation-pacing` | Pool budget before fill; opening guarantees; independent access/combat/grind assumptions; generation preview; short/standard/extended presets; pacing reports. | Fresh-start opening and measured pacing |
| 40 | `codex/expansion-two-hardening` | Full option/category matrix, multiworld/restart/rollback, resource/UI/package parity, docs and evidence reconciliation. | Owen's complete acceptance matrix and calibration |

Each PR builds on the previous branch. Add fixes without rewriting published
history. Run the complete verifier and inspect Windows/Linux CI for every head.
Use independent tooling runtimes; never change installed source, local developer
panel, protected multiplayer trees or running AP sessions for these PRs.

The [delivery index and native acceptance matrix](expansion-two-acceptance.md)
link the stacked PRs and distinguish source automation from Owen's remaining
game verification and balance calibration.

## Options and semantics

New gameplay systems are explicit APWorld choices in validated slot data and
configuration. Presentation options never create receipts or checks. Disabling
a reward system leaves its AP-specific restrictions inactive. Added legacy/default
values preserve existing configuration digests. Non-default new settings require
a matching world/client/add-on bundle and a newly generated seed.

- PDA tracker: enabled/disabled; region/status filters are local display state.
- Hints/scouting: selectable; reward previews off by default. A preview is real
  server item metadata, never an item receipt.
- Shop/faction checks: independent finite, stable service milestones; repeated
  purchases cannot create an infinite item farm.
- Discovery mode: existing per-type checks or first-N-distinct quota checks.
  A mutant quota of 15 gives one fixed milestone check for each of the first 15
  qualifying distinct species, regardless of which species are found. Repeated
  kills of one species do not advance it. Exclusions remove rare/friendly targets.
- Rare/missable policy: include selected checks, omit them, or exclude required
  progression. Normal presets avoid forced hostility and fragile mortal-NPC tasks.
  Solver reachability cannot guarantee ALife availability.
- Progressive tools, workshop/recipe access, permission supplies, supply package
  categories and convenience rewards are independent reward selections.
- Access, combat assumptions and grind thresholds are independent choices.
  Challenge starts are explicit; ordinary survival supplies remain available.

## Tracker and delivery

Completed means an observed/saved or server-confirmed check. Available means its
documented AP requirements are met, not that a random encounter or NPC exists.
Blocked entries explain missing access, protection, equipment or quest permissions.
Do not expose disabled checks or unscouted rewards. Track goals and important
permissions even when their check category is off. Show local completion, server
confirmation and item application as distinct facts where reported.

Show known receipt total, applied count, pending reward and failure reason.
Coordinates received, cache claimed and supplies created are different states.
A write/scout never acknowledges an item. Permanent unlocks and consumable plans
retain separate recovery semantics. Offline data cannot claim a live connection.
No-PDA starts keep the bridge and Archipelago broadcasts working. PDA-only
screens remain unavailable until restoration.

## Pool and pacing

Calculate mandatory rewards from gates/goals before useful items/filler. Validate
capacity, progressive copies, local constraints and precollected items. Never
truncate a required permission. Protect a usable opening with deterministic checks
and alternatives; a starting tool, weapon or PDA cannot require its own use.
Keep early essentials locally available where necessary and preview the guarantee.

Preview enabled counts/regions, progression budget, useful/filler counts, starting
routes, exclusions, quotas and demanding combinations. Distinguish a settings
preview from an actual seed placement report. Existing time estimates remain
uncalibrated until measured runs establish coefficients; spheres/check counts do
not measure walking, repair or random-spawn waiting.

## Acceptance

Counts below record each original implementation increment. The subsequent
[merge review](expansion-two-merge-review.md) adds compatibility integration and
regressions; each linked PR records its reviewed head's updated verifier/CI results.

| Step | Source and automation | Native |
|---|---|---|
| 31 | Implemented; full verifier passed (826 tests) | Not run |
| 32 | Implemented; full verifier passed (895 tests) | Not run |
| 33 | Implemented; full verifier passed (923 tests) | Not run |
| 34 | Implemented; full verifier passed (935 tests) | Not run |
| 35 | Implemented; full verifier passed (944 tests) | Not run |
| 36 | Implemented; full verifier passed (968 tests) | Not run |
| 37 | Implemented; full verifier passed (981 tests) | Not run |
| 38 | Implemented; full verifier passed (988 tests) | Not run |
| 39 | Implemented; full verifier passed (1,034 tests) | Not run; calibration pending |
| 40 | Implemented; full verifier passed (1,041 tests) | Not run; release gates remain |

Research references inspected 19 November 2026, used as design ideas rather than
Anomaly API evidence:
[Subnautica](https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/subnautica/options.py),
[Raft](https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/raft/Options.py),
[Stardew](https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/stardew_valley/options/options.py),
[DS3](https://nex-3.com/ds3/info/),
[7 Days to Die](https://github.com/OrcThrowman/7-Days-to-Die-AP),
[Monster Hunter Rise](https://github.com/HillbillyDroid/MHRise-APWorld).
