# Expanded randomiser: staged checklist

**New scope, 19 November 2026:** the [second expansion plan](expansion-two-plan.md)
adds Steps 31–40 as stacked PRs starting with the PDA tracker. It includes reward
options, scouting, regional/delivery displays, discovery quotas, opening protection
and pool/pacing previews. This extends the historical status below; native
verification remains Owen's, with no automatic deployment or game launch.
See the [stacked delivery and remaining acceptance](expansion-two-acceptance.md)
for the new scope; the dated counts and merge states below describe the earlier
thirty-step implementation.

Updated **19 November 2026**, after the individual reviews and merges of PRs
#2–#35, through merged implementation `ddb9ee8`. All thirty core increments and
the local generator are merged in source. This checklist/audit reconciliation is
PR #36. Expanded deployment and in-game acceptance remain pending.

Checkboxes below describe the action on that line: **implemented**, **automated
test passed**, or **in-game acceptance recorded**. A checked implementation or
mock/server test does not close an unchecked engine acceptance item. Every stage
still has an open engine/release exit gate. Earlier pilot acceptance stays valid
on its stated evidence basis.

## Current status at a glance

| Stage | Implemented / automated evidence | Still to validate or finish |
|---|---|---|
| 0 — pilot and inventory | User-accepted pilot reload/third-map trigger; source/roster inventory | Independent remaining reward/goal capture, live recovery, callback probes and baseline compatibility |
| 1 — PDA and recovery | Named transfers, bounded queues, deduplication and real AP restart tests | Actual PDA history/rendering, no-PDA restoration and game recovery |
| 2 — options and exploration | 14 check / 7 reward options, starting loadouts, 33 maps, 18 settlements | Actual map/hub entries, starter variants and extra-transition coverage |
| 3 — activity checks | Mutants/factions, artefacts, quests/story, equipment and rank adapters | Native credit/provenance, milestone semantics, encounters and saved counters |
| 4 — stash, reputation, skills | White/orange stashes, goodwill and Haruka adapters | Actual containers/claims, trader tiers, stats and integration compatibility |
| 5 — permissions and travel | Quest/equipment/zone keys, native guards, optional travel and solver rules | Every entry route, real permission enforcement and travel safety/recovery |
| 6 — goals | All five alternate goals plus development tour; generator/server regressions | Actual qualifying condition and completion packet for each goal |
| 7 — balance/release | Six presets, 6,000-seed matrix, recovery/package hardening and private candidate | Playthrough balance, performance, install/upgrade/removal, independent review and release gates |
| Additional — local generator | Presets, catalogues, estimates, YAML/seed downloads and browser recovery tested | Playtime calibration against real runs; general engine acceptance is separate |

Latest complete automation: **756 tests passed** (719 covered Python/Lua,
32 untraced generator/server, five Node frontend). All owned Python runtime
modules measured 100% lines/branches; Lua executable-line gates passed, without
a Lua branch or numeric JavaScript coverage claim. Windows/Linux push and PR
checks passed on every reviewed implementation head. See the
[verification record](verification-record.md), [merge audit](merge-review-record.md)
and [PR #35 checks](https://github.com/Lolager23/gamma-archipelago/pull/35/checks).

Foundation PR #1 had already merged. PRs #2–#35 were subsequently reviewed,
fixed where needed, fully verified and merged individually into main. PR #3
(MCM) and #4 (plan) precede Steps 01–30 (#5–#34); #35 adds the local web app.
Probe PR #2 remains a separately packaged diagnostic component. The audit records
reviewed heads, merge commits and fixes. Use the [exact PR index](implementation-status.md).

## What is next

1. When Owen is ready for acceptance, close the development game/client/server,
   back up the entire
   appdata/profile/configuration trees, and deploy matching world/client/add-on
   revisions only into the isolated development installation. Follow the
   [development guide](development-guide.md), using MO2 and fresh Loner/Cordon
   acceptance saves. Do not reuse the normal multiplayer installation or saves.
2. Start with pilot recovery/callback evidence, then PDA incoming/outgoing/self
   messages. Continue through exploration, activity checks, rewards, locks/travel
   and goals using each step's acceptance document. Record commit, seed/preset,
   baseline, result and evidence; fix failures with reproducing regressions.
3. Complete the release matrix: two fresh MVP runs, a real in-game mixed
   multiworld, every alternate goal, migration/recovery and performance. A goal
   demonstrated during an MVP run can also supply that goal's evidence.
4. Fix acceptance failures on focused branches with reproducing regressions,
   then rerun the affected native acceptance against the matching bundle.
5. Close the independent human review/licence/compatibility gates before any public v1 decision.
   The existing archive is a private, unaccepted candidate, not a public release.

Owen reserved engine verification for after each merge and requested no further
automated game launches. This update launches nothing, deploys nothing and does
not infer that a feature is already installed from its source implementation.

## Remaining implementation/polish and supported limits

No numbered core implementation branch remains unstarted or unmerged. Follow-up
coding is driven by the open acceptance cases, with these limits explicit:

- [x] Implement PDA grammar polish and translation-ready English resources.
  Whole-sentence game-language templates use quoted labels and English fallback;
  native rendering and any future language pack remain user acceptance.
- [ ] Calibrate playtime and reward/progression balance using recorded runs;
  current estimates are adjustable, uncalibrated scenarios.
- [ ] Resolve baseline third-party failures that affect a supported integration;
  four failures were classified, not repaired by the AP stack.
- [ ] Fix any defects found in post-merge engine acceptance and repeat affected
  regressions/acceptance. Their existence or severity is not assumed in advance.

The bounded candidate uses 27 white stash types in a finite Cordon container
roster, one protected orange psi-helmet claim, three quest-chain permissions,
four Haruka skills and nine curated travel hubs with fallback. These are not
arbitrary progression-stash placements, every native quest stage, or universal
support for other skill/engine mods. Zone-key placement uses a local randomized
exploration chain; other rewards can cross players. Native encounter/task
availability and other faction/start routes still need engine evidence. In-world
co-op, transition randomization, DeathLink and the other
[stretch goals](randomisation-plan.md#exploratory-stretch-goals) remain separate,
unimplemented investigations, not checked-off candidate features.

Generation does not inspect the receiving game's installed mod versions. Runtime
guards keep incompatible skill/reward application pending; actual dependency and
winning-script compatibility must be established before accepting that integration.

## Verified starting point

- [x] Isolated Anomaly/GAMMA installation and MO2 development profile exist.
- [x] Three-region pilot and inventory rewards are implemented and deployed.
- [x] Rostok check reached the local server and awarded a Bandage.
- [x] Garbage check reached the local server and awarded a Basic Toolkit.
- [x] The server's on-disk save contains both checks and both item receipts;
  the game's outgoing bridge acknowledges two applied items.
- [x] User confirmed the MCM toolkit button and live checks/rewards work.
- [x] Third-map acceptance closed by the user on 19 November, based on the
  shared working trigger code; an independent Cordon server capture is not claimed.
- [x] Ordinary game save/reload validated by the user on 19 November.
- [ ] Independently capture the third reward and pilot goal packet.
- [ ] Record older-save rollback and client/server reconnect/restart cases.

These earlier observations are from the deployed `a7995ef` add-on on the MCM
branch; they do not validate the later expanded implementation. The detailed
[verification record](verification-record.md) separates engine, server and user
evidence. A received-item counter is not proof that every game save reloads safely.

## Configuration contract

The sections below retain the requested acceptance contract. Each listed
category now has an independent APWorld generation option; the public names
were fixed in the options branch. Optional categories default off, and six
explicit presets are provided. A preset enabling a feature does not establish
its engine acceptance. Step documents own the implemented roster and limits.

Generation determines enabled checks, thresholds, reward pools, goal, starting
access and rule assumptions. Export that manifest in `slot_data` and validate it
before applying it in the game. Changing MCM settings must not change a generated
seed's checks, rewards or gates. MCM may configure presentation and connection UI.

Disabled check categories produce no AP locations. Disabled reward categories
produce no corresponding AP items and impose no associated AP locks on ordinary
gameplay. Goal detection remains active even if its related check category is
off. A goal is not an extra shuffled location unless explicitly modelled as one.

Generation must reject all-checks-off, insufficient locations for mandatory keys,
unreachable goals and incompatible starts/integrations with an actionable error.
Do not remove mandatory keys to make a small pool fit. Fill remaining locations
with bounded supplies; do not require every reward category to be enabled.

## Optional starting-gear restrictions

Independent APWorld options now control the starting loadout, defaulting to the
ordinary supported loadout. These are seed-generation settings, not edits to a
running save. The chosen loadout is frozen in slot data.

| Equipment group | Restricted-start contract |
|---|---|
| Detector | No starting detector; advanced detection checks require later access. |
| PDA | No starting PDA; restore its map/task functionality when acquired/unlocked. |
| Firearms | No starting guns. Treat their ammunition separately. |
| Knife/melee | No starting knife or other melee weapon, independently selectable. |
| Armour and headgear | No starting outfit and/or helmet, with separate selections. |
| Backpack | No starting backpack; account for actual carrying-capacity effects. |
| Tools | No starting toolkit/repair equipment, with explicit item groups. |
| Utility equipment | Optional no binoculars, flashlight or other inventoried starter utilities. |
| Supplies and money | Optional reduced/zero ammo, medicine, food or starting money, each independently configured. |

Provide a **No Starting Weapons** preset that removes both firearms and melee
weapons, and a separate **No Starting Firearms** selection that keeps a knife
unless its own restriction is enabled. Publish the exact affected item groups;
do not infer weapons or armour from item names, weight or price.

For durable equipment, the implemented modes are:

- **Normal:** use the ordinary starting loadout and ordinary acquisition rules.
- **Absent at start:** omit the initial item; later looting, buying and using it
  work normally. This does not create a permanent equipment permission gate.
- **Locked until AP unlock:** omit the initial item and gate the corresponding
  equipment capability until its AP reward is applied. Enforce this with
  explicit acquisition/use rules; finding a physical item must not bypass the
  chosen permission lock. The unlock supplies a documented usable baseline item
  where needed, rather than leaving the player with an unusable permission.

Use omission/quantity settings for consumables and money, not permanent bans on
food, medicine or ammunition. Add a separately selectable
`rewards_starting_gear_unlocks` category for delayed equipment permissions; this
is the seventh reward category, in addition to the six previously requested.
Generation rejects an AP-locked start if its required unlock rewards are disabled
or do not fit the selected check pool. Absent-at-start mode needs no AP unlock.

Prefer changing the authoritative initial-loadout grant before inventory is
created. If the engine needs a fallback removal step, run it exactly once before
AP deliveries and persist its completion. Never repeatedly strip inventory on
load, respawn or reconnect; preserve earned, traded, crafted and AP-delivered
equipment. Verify faction defaults, custom loadout purchases, difficulty presets,
tutorial grants and any refunds so none bypass or duplicate the restriction.

No-PDA starts must not stop the AP bridge, lose pending messages or prevent the
PDA unlock from being received. Keep connection/recovery status available in the
companion and an appropriate menu. Deliver Archipelago broadcasts without
requiring a PDA, including join, received-reward and sent-reward notices. Do not
expose a restricted map or task screen accidentally through another UI or keybind.

The world must model the missing capabilities: no detector cannot imply early
detector-dependent artefact access; no weapons cannot imply early combat checks;
no PDA cannot imply early PDA-dependent jobs, maps or stash interactions. Check
combined restrictions and full multiworld progression spheres. Guarantee viable
early checks and recovery equipment without depending on lucky loot or an item
behind its own requirement. Reject unsupported unsafe starts clearly.

## Checks: requested categories and acceptance triggers

All checks are finite and monotonic. Threshold lists are sorted, unique and capped
at generation time. A repeatable activity never becomes an unlimited check farm.
Keep the three published pilot location IDs and never recycle an ID.

| Option | Trigger and completion rule | Investigation and acceptance |
|---|---|---|
| `checks_maps` | One first-arrival check for every supported playable map, including underground maps. Loading or starting there counts. | Inventory actual level IDs; exclude menu/test levels explicitly. Keep the existing Cordon/Garbage/Rostok IDs. Verify every entry through the engine. |
| `checks_settlements` | First physical entry into a defined major-settlement volume on its map. | Curate named hubs, stable coordinates and radii; a map visit alone is insufficient. Repeated entry and overlapping volumes must not duplicate a check. |
| `checks_mutant_first_kills` | First credited kill of each canonical mutant species. | Use explicit variant-to-species mappings; a stronger variant is not a new species unless deliberately listed. Test actor attribution, summons and environmental deaths. |
| `checks_faction_first_kills` | First credited kill of a nonessential stalker from each supported faction, using the victim's faction at death. | Separate from mutants. Define hostile/neutral attribution and faction changes. Never require killing a story-critical NPC; validate any faction/start restrictions. |
| `checks_artefacts` | First acquisition of each supported artefact type. | Record canonical sections and aliases. Define pickup/trade/crafting sources explicitly; prevent drop/pickup repeats and AP-injected feedback. Condition variants do not become accidental extra types. |
| `checks_quest_types` | First successful completion of each supported normalized task type, such as delivery, retrieval or hunting. | Map actual task templates to types. Acceptance, cancellation, failure and reward collection are distinct events; choose one authoritative completion event. |
| `checks_gear_upgrades` | First successful installation at each defined equipment-upgrade milestone. | Confirm the upgrade was installed, not merely offered or paid for; distinguish repair, crafting and upgrade services. Bound the milestone roster. |
| `checks_armour_tiers` | First use of an outfit in each curated light/medium/heavy tier. | Tier comes from an explicit equipment manifest, not item weight. Validate equip state, disguises, damaged gear and powered armour requirements. |
| `checks_weapon_tiers` | First use of a firearm in each curated weapon-class/tier milestone. | Publish category and tier definitions; calibre, sale price and damage alone are not reliable tier measures. Test pistols, shotguns, rifles and specialist weapons. |
| `checks_knife_tiers` | First equip of each better knife tier in the curated progression. | Preserve acquired high-water mark; re-equipping or downgrading cannot repeat a check. |
| `checks_kill_milestones` | Reach each configured cumulative kill threshold. Initial test profile: 10, 25, 50, 100. | Count each credited victim once. Define mutants versus stalkers as a separate filter. Default to direct actor kills; do not silently credit companion kills. |
| `checks_side_task_milestones` | Complete each configured cumulative side-task threshold. Initial test profile: 5, 10, 20, 40. | Count each task instance once, excluding failed/cancelled jobs and story tasks. Distinguish a repeatable template from a unique task instance. |
| `checks_story_milestones` | Complete curated, named story milestones. | Verify persistent info portions/task state and supported faction variants. Dialogue proximity, a quest being accepted or an NPC spawning does not prove completion. |
| `checks_rank_milestones` | First reach of each supported Stalker Rank threshold. | Read the active rank mod's thresholds and retain the highest reached rank. Rank loss or repeated load must not create extra rewards. |

The thresholds above are starting test values, not final balance commitments.
Maps, settlements, species, factions, artefacts, quest types, equipment tiers,
story milestones and ranks each require a versioned content manifest before
their full category can be enabled. Missing hooks remain tracked work; do not
silently remove a requested category after a failed probe.

## Rewards: required categories and behaviour

| Option | Reward behaviour | Required constraints |
|---|---|---|
| `rewards_loot_stashes` | Reveal a white stash coordinate containing basic or higher-tier nonessential loot. | Seeded quality tiers and loot families; include ammo-calibre families where supported. Explicitly interpret stash calibre as both quality and optional ammo specialization. No required key is hidden in a filler stash. |
| `rewards_progression_stashes` | Reveal an orange stash coordinate with guaranteed, seeded progression contents. | Stable stash identity, reachable placement, protected contents, one claim and recoverable save state. Colour supplements a text label. Model access and local collection of its key in world logic; the coordinate alone is not possession of the key. |
| `rewards_quest_keys` | Grant named, persistent permissions for selected quest stages. | Gate the actual quest transition, not only its dialogue label. Suppress ordinary bypasses only for enabled AP gates. Preserve prerequisite dialogue, NPC availability and story safety. |
| `rewards_faction_reputation` | Grant bounded reputation/goodwill increases for selected factions, enabling documented trader tiers. | Verify the actual trader eligibility calculation. Do not equate reputation with faction friendship or override story hostility. Clamp gains and reconcile permanent AP bonuses after reload. |
| `rewards_stat_levels` | Grant named character-skill levels through the supported stat mod. | Start with the installed Haruka Skill System plus GAMMA's balance override. Use a dedicated adapter, respect caps and recalculate effects through its API. Refuse this option if the compatible integration is absent. |
| `rewards_zone_keys` | Grant permanent access to named zones and an optional first-arrival fast-travel opportunity. | Enforce every supported entry route and preserve a return route. See the travel policy below; an AP key does not automatically grant physical psi/radiation protection. |
| `rewards_starting_gear_unlocks` | Restore selected equipment capabilities omitted and locked by the starting-loadout options. | Only create the required unlocks for selected AP-locked groups. Supply documented baseline equipment, enforce the chosen permission, and reconcile it after save/load. |

Provide explicit sets/ranges for stash quality, ammo families, reputation factions,
skill rewards and finite quantities. The pool must contain every required key and
must fit the selected check count. Existing supplies can remain filler. Detector,
toolkit and psi-protection candidates remain in the broader design and must have
defined acquisition rules when a goal depends on them.

For orange stashes, use a finite catalogue of vetted containers or an additive
stash implementation. Do not overwrite arbitrary player/NPC containers. Content
must not reroll, disappear because the box was previously empty, or grant a second
copy after loading. A local stash-claim event can award its internal progression
key without creating an unplanned second AP check or item.

Zone-key travel acceptance policy: one optional trip on unlock to one designated
safe settlement in the newly unlocked zone, once other protection/story
requirements are met. Never teleport automatically. For a zone without a viable
hub, offer an already unlocked safe settlement instead. Persist eligibility and
consumption; show the chosen destination. Resolve hostile hubs, unavailable
guides, fees, current fast-travel restrictions and extra-transition mods before
accepting this policy. The curated-hub implementation still requires engine validation.

## PDA reward messages: first feature increment

| Event | Player-facing text |
|---|---|
| Physical reward received and applied | `{PlayerName} gave you a {ItemName}` |
| Permission, zone, quest or skill unlock applied | `{PlayerName} unlocked your {UnlockName}` |
| Our check sends a physical item to another slot | `You gave {RecipientName} a {ItemName}` |
| Our check sends a known permission/unlock | `You unlocked {RecipientName}'s {UnlockName}` |
| Our check awards our own slot | One received/applied message, without a second outgoing copy |

Use grammar-aware localized templates for plurals and names that do not take
an article. Names are AP slot display names, not the stalker's in-game identity.
Use a sender label such as Archipelago for server/start-inventory grants.

The pinned AP protocol exposes sender/location/item metadata in `NetworkItem`
and recipient information for `PrintJSON` ItemSend messages. Preserve structured
metadata in the companion instead of scraping the human-readable log. Resolve
foreign-game item names through that recipient game's data package. References:
[network protocol 0.6.8](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/docs/network%20protocol.md),
[CommonClient 0.6.8](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/CommonClient.py).

The original pilot bridge carried item IDs only. The implemented stack adds a
versioned metadata/notice channel with legacy compatibility regressions.
Incoming messages occur after successful in-game application;
queued or failed rewards must not announce success. Outgoing messages require
server confirmation of a transfer from our slot, not just a local check write.
Do not claim the other game's item has physically applied.

Persist stable transfer identities and notification acknowledgements, independently
of reward receipt counts. Deduplicate replays, reconnects, overlapping histories
and duplicate PrintJSON packets. Reconstruct confirmed outgoing transfers after
offline play from authoritative checked-location data/scouting if necessary;
do not assume transient PrintJSON announcements form a durable history. Test
self-rewards, multi-item checks, start inventory and alias changes. A failed PDA
display must not cause the underlying item to be granted twice.

Queue messages while no living character is loaded, deliver in bounded batches,
and retain them in PDA history where the installed API supports it. Sanitize and
bound names/text, preserve supported Unicode, and escape PDA formatting controls.
Use the game's news/tip API with a recognizable Archipelago sender/icon. The
installed `news_manager.send_tip` and `db.actor:give_game_news` are source leads;
actual PDA history, sound and visibility still require engine probes.

For foreign games, an item's AP progression flag does not universally mean it is
a permission. Use "unlocked" only for explicitly known unlock semantics; use
"gave" for other items, including foreign progression items with unknown type.

## Alternate goals

Expose `goal` as a choice. Keep the three-map tour as a development goal, then
add each requested goal separately. Do not silently fall back to a different goal.

| Goal | Actual completion requirement | Logic and validation |
|---|---|---|
| Get Psi Protection | Acquire the explicitly supported, working psi-protection item/unlock and verify it is usable. | Freeze qualifying variants and calibration state. A queued AP receipt or unrelated psi-resistance stat alone is insufficient. |
| Disable Brain Scorcher | Reach the persistent, verified shutdown state. | Verify switch/task/info-portion identity and every access/protection requirement. Merely entering Radar or the bunker is insufficient. |
| Meet Strelok | Complete the canonical encounter/dialogue milestone. | Verify the supported story route; proximity, NPC spawn and dialogue opening are insufficient. |
| Living Legend | Complete the terminal milestone of the Living Legend story chain. | Separate from Meet Strelok. Inventory every prerequisite and any faction/start restriction. |
| Visit all X-Labs | Physically enter every named lab in a frozen, visible goal roster. | Inventory the installed build's actual lab names and level/volume IDs before fixing the roster. Do not assume every underground level is an X-Lab. Preserve access to every required lab. |

Goal observation is independent of optional AP check categories. The generator
must still model its prerequisites. If a required reward category is disabled,
keep a verified ordinary acquisition route; if no valid route exists, reject the
configuration. When gating is enabled, remove or reconcile ordinary bypasses.

## Execution checklist and branch order

See the [PR index](implementation-status.md) for the completed branch boundaries
and each linked step document for source details. Implementation/automated work
is ticked below; actual engine exit conditions remain open until recorded.

### Stage 0: close the pilot and inventory compatibility

- [x] Third-map trigger and ordinary game save/reload accepted by the user;
  see the verification record for confirmation versus captured evidence.
- [ ] Independently capture the remaining reward and actual goal packet.
- [ ] Verify disconnect/reconnect and wrong-seed refusal in a disposable dev save.
- [x] Record the pinned GAMMA/engine/AP baseline and inspect active source winners.
- [x] Classify the four existing third-party script failures.
- [x] Inventory the supported content, callbacks/info portions, credit rules,
  task identities, equipment tiers and five-lab roster (Steps 02, 07–13, 26).
- [x] Inspect starter grants, faction/difficulty loadouts and PDA dependencies;
  implement the documented fresh Loner/Cordon acceptance baseline.
- [ ] Confirm current MO2 winners and observe callback arguments/save behaviour
  on the installed build using the [probe checklist](callback-probes.md).
- [ ] Resolve any classified baseline failure affecting a supported adapter;
  test other faction/difficulty/custom-loadout variants before claiming support.

Exit: repeatable pilot evidence and a finite manifest/probe backlog; no claim that
current inventory receipts prove crash-safe recovery.

### Stage 1: PDA messages and durable session recovery

- [x] Preserve sender, recipient, foreign item name and known unlock kind.
- [x] Implement versioned metadata, English incoming/outgoing PDA notices,
  self-reward deduplication and bounded broadcast queues (Steps 03/04/19).
  Broadcasts now work without a PDA, including omitted and AP-locked starts.
- [x] Verify notice attribution/deduplication, confirmed transfers and durable
  server/client recovery in mocked game and real AP server tests.
- [x] Document rollback/replay policy, separating permanent unlocks from
  consumables; older-save consumable replay remains an explicit limitation.
- [ ] Observe actual PDA text/history/sound, correct names and one self-notice
  in GAMMA, including delayed display after restoring a PDA.
- [ ] Verify game/client/server restart, offline checks, old-save rollback and
  failed reward/display handling in disposable development saves.
- [x] Finish translation-ready templates and English article/plural/name polish.
  See [PDA messages](pda-reward-messages.md); native visual acceptance is not run.

Exit: a live two-player or mixed-game test proves both directions and names;
reconnect/load do not spam or create rewards twice because a notice failed.

### Stage 2: options, catalogue and exploration

- [x] Implement 14 check / 7 reward options and typed, versioned slot data.
- [x] Implement nine gear modes/groups, four supply percentages, No Starting
  Weapons and the restricted preset; starter omission is once before AP grants.
- [x] Add all 33 supported map arrivals, preserving the three pilot IDs.
- [x] Add 18 curated settlement checks using native smart-terrain entry volumes.
- [x] Build the curated baseline region graph and generation/access rules.
- [x] Test disabled-category isolation, all-off rejection, category singles/pairs,
  preset settings and required-pool sizing (Steps 05–08/27).
- [ ] Observe every supported map/hub trigger in the engine, including overlap,
  starting/loading there and disabled-category behaviour.
- [ ] Compare the graph and native route guards against all installed extra
  transitions; demonstrate starter variants and preservation of earned gear.

Exit: all map/settlement checks can be generated and demonstrated, with no checks
leaking from disabled categories and no IDs depending on option order.

### Stage 3: combat, collection, tasks, equipment and rank

- [x] Implement independent first-kill rosters: 25 mutants and 13 factions.
- [x] Implement finite cumulative kill thresholds with credit/deduplication rules.
- [x] Implement 66 artefact acquisitions and mocked provenance/replay tests.
- [x] Implement 13 quest types, finite side-task totals and 53 story checks.
- [x] Implement 20 upgrade/armour/firearm/knife milestones and eight rank checks.
- [x] Save monotonic counters/sets and test duplicate, downgrade/reset and
  save/load behaviour through the Lua harness (Steps 09–13).
- [ ] Demonstrate native attribution/provenance, actual task completion, equipment
  semantics and ranks; cover negative triggers and AP-injected feedback.
- [ ] Verify saved counters across actual reload/death and establish that required
  species, factions, artefacts/tasks and NPCs remain obtainable on supported runs.

Exit: every check category has a fixed roster, engine evidence and corresponding
AP reachability assumptions. Active quests or naturally earned skill gains must
not create unbounded feedback through AP rewards.

### Stage 4: stash, reputation and skill rewards

- [x] Implement 27 white stash quality/ammo-family types in the finite Cordon roster.
- [x] Implement the protected orange Cordon psi-helmet stash and local claim event.
- [x] Implement bounded goodwill for eight factions and native trader eligibility.
- [x] Implement four Haruka skill rewards with cap/API guards and recalculation.
- [x] Classify effects and test planned receipts, retries, caps, save state and
  uncertain native creation outcomes separately (Steps 14–17/29).
- [ ] Inspect actual white/orange markers, physical containers/contents and saved
  claims, including empty/previously used caches and failed native grants.
- [ ] Demonstrate native trader-tier changes and actual Haruka stats/UI, including
  missing/incompatible integration and capped rewards.
- [ ] Validate each reward recovery policy in the engine; mock idempotence does
  not establish exactly-once item creation across a crash/save boundary.

Exit: direct grants and stash contents survive save/load under the documented
policy, and disabled categories impose no new locks or missing dependencies.

### Stage 5: quest and zone keys

- [x] Implement three quest-chain keys and deferred native task-grant replay.
- [x] Implement nine AP equipment permissions, baseline grants and deferred
  PDA map markers.
- [x] Implement 32 zone keys with native/scripted transition guards and a local
  randomized exploration chain; Cordon remains the free starting region.
- [x] Implement preview/confirmation and saved one-trip consumption for nine
  curated hubs with safe fallback and native travel restrictions.
- [x] Model equipment, psi protection, stash/PDA and story access in AP logic;
  reject insufficient pools and test self-locks and bounded recovery.
- [x] Exercise restricted starts, hostile/unavailable hubs, native route guards,
  purchased/scripted inventory and save/load with mocks (Steps 18–21/27/29).
- [ ] Demonstrate quest progression enforcement and every supported actual entry
  route, including extra transitions/guides and packet-hook same-zone fallback.
- [ ] Play no-detector/no-PDA/no-weapons starts alone and combined; verify early
  checks, restored capabilities, starter grants, bought/looted gear and messages.
- [ ] Verify hostile/missing hubs, one-time travel, protection/story restrictions,
  death/locked-zone loads, rollback and native-disable ownership in the engine.

Exit: game enforcement matches generator access rules; no progression key is
placed behind itself and every supported configuration has a completion route.

### Stage 6: five goal choices

- [x] Implement Get Psi Protection using the usable calibrated-helmet condition.
- [x] Implement Brain Scorcher using its native shutdown state.
- [x] Implement Meet Strelok using the canonical completed first dialogue.
- [x] Implement Living Legend using the terminal story milestone.
- [x] Implement All Labs using X18, X16, X19, X8 and War Lab; ordinary underground
  maps do not count (Steps 22–26).
- [x] Test goal/category independence, premature completion guards, solver gates
  and actual AP completion packets with synthetic game snapshots.
- [ ] Record a real qualifying condition and completion packet for each of the
  five goals, without premature/repeated completion, on supported fresh saves.
- [ ] Confirm actual story/faction prerequisites and local goal observation when
  related check categories are disabled.

Exit: one fresh successful engine playthrough per supported goal, plus regression
tests for premature completion, disabled related check categories and lost packets.

### Stage 7: balance and release

- [x] Commit six presets/YAML examples, supported limits and rejected combinations.
- [x] Run 1,000 deterministic seeds for each preset, category singles/pairs and
  targeted full-option goal/gate tests; keep Windows/Linux CI green.
- [x] Implement real-server mixed-game/restart tests, strict save/identity checks,
  legacy compatibility, portable packages and archive loading (Steps 28/29).
- [x] Document compatibility, rollback/removal limits and third-party licence
  boundaries; prepare and hash-check the private unaccepted candidate (Step 30).
- [ ] Complete two fresh MVP playthroughs and a real mixed-game multiworld.
- [ ] Verify actual clean install, upgrade/migration and save recovery. Removal
  from an active gated campaign is unsupported; test documented backup restore
  or a clean non-AP save instead of promising arbitrary live uninstall.
- [ ] Measure callback/poll cost and notification bursts on the pinned build.
- [ ] Complete independent human review/playtesting, compatibility sign-off,
  licence choice and final accepted release documentation/checksums.
- [ ] Obtain a separate v1 publication decision before tagging/releasing; no
  public release or repository visibility change has been performed.

Exit: every supported requested category and goal has implementation, tests and
engine evidence; unresolved features are labelled and discussed rather than
advertised as complete. Multiplayer here means Archipelago multiworld; in-world
xrRazom co-op remains a separate investigation and installation.

### Additional delivery: local APWorld generator (PR #35)

- [x] Implement local preset/category/loadout/goal controls and exact searchable
  check/reward projections using the shared configuration/catalogue core.
- [x] Implement adjustable goal/full-clear/session estimates with explicit
  assumptions, player YAML export and actual local seed ZIP generation.
- [x] Validate six preset displays, 64-bit seed limits, repeatability, exact
  generated manifests, concurrent-generation refusal and later recovery.
- [x] Reproduce/fix draft-loadout overwrites, stale totals, reserved/trimmed names,
  incomplete requests and the lost-backend banner; add five frontend regressions.
- [x] Exercise real browser ZIP/YAML downloads, search, milestone/name/seed
  validation, backend stop/restart and the responsive layout.
- [ ] Calibrate playtime ranges and useful reward/progression balance with real
  GAMMA runs. Browser/server acceptance does not close engine gates above.

The app is **local-only**, as requested. See its [guide](generator-web-app.md)
and the latest [QA evidence](verification-record.md). No hosted deployment is planned.

## Structure and verification rules

Keep a single game-state owner and a single client session coordinator. Add small
adapters for exploration, combat, collection, tasks, equipment, stash rewards,
reputation, skills and access. Call them directly through explicit dependencies;
do not introduce an event bus, service locator or distributed reward authority.
Keep content manifests with the authoritative catalogue and generate Lua copies.

Every implementation PR needs regression tests for its behaviour, per-module
Python coverage of at least 95% lines/branches and 100% for protocol/session
identity and receipt ordering. Require at least 95% Lua executable-line coverage
and explicit decision tests; do not claim Lua branch coverage. Use real AP
generation/server tests and separate engine evidence. Run Windows and Linux CI.

Across categories, test wrong seed/slot, missing integration, duplicate and
out-of-order events, load/reconnect, older-save rollback, disabled options,
unreachable content, failed reward application and unchanged unrelated progress.
Keep game assets, saves, runtime manifests and private evidence outside Git.

## Evidence sources and limits

The installed baseline exposes item acquisition and NPC/mutant death callbacks
in `axr_main.script`; these are leads for the callback-probe branch, not proof of
all desired attribution semantics. The installed Haruka script exposes
`increase_skill` and `level_up_skill`, and GAMMA overrides skill balance. Verify
the winning scripts, caps, recalculation and saved fields before using them.

World configuration and reachability follow the pinned
[AP World API](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/docs/world%20api.md)
and `Options.py`, not a runtime-only menu switch. See [resources](resources.md)
for source references. Known broken optional compatibility scripts in the current
GAMMA baseline are tracked in the verification record; this planning change does
not patch or enable third-party components.
