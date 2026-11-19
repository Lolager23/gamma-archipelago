# Expanded randomiser: staged checklist

Requested 18 November 2026. This is the implementation plan, not a list of
features already available. This increment changes documentation only. The user
explicitly selected verification and planning rather than implementing PDA
messages now. Keep the existing local pilot running on its present schema.

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

These observations are from the deployed `a7995ef` add-on on the MCM branch;
they are not new functionality in this documentation branch. The detailed
[verification record](verification-record.md) separates engine, server and user
evidence. A received-item counter is not proof that every game save reloads safely.

## Configuration contract

Every category below gets an independent APWorld generation option. Names here
are proposed public names, to be frozen during the options branch. New categories
start disabled until their branch meets acceptance. Provide Pilot, MVP and Full
presets with explicit YAML examples; do not silently enable untested features.

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

Add independent APWorld options for the starting loadout, all defaulting to the
ordinary supported loadout. These are seed-generation settings, not changes to
the current pilot or a running save. Freeze the chosen loadout in slot data.

| Equipment group | Proposed restricted start |
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

For durable equipment, distinguish these proposed modes:

- **Normal:** use the ordinary starting loadout and ordinary acquisition rules.
- **Absent at start:** omit the initial item; later looting, buying and using it
  work normally. This does not create a permanent equipment permission gate.
- **Locked until AP unlock:** omit the initial item and gate the corresponding
  equipment capability until its AP reward is applied. Implement this later with
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
companion and an appropriate menu. Queue PDA-only notifications/history while
locked, then deliver them in bounded batches after restoration. Do not expose a
restricted map or task screen accidentally through another UI or keybind.

The world must model the missing capabilities: no detector cannot imply early
detector-dependent artefact access; no weapons cannot imply early combat checks;
no PDA cannot imply early PDA-dependent jobs, maps or stash interactions. Check
combined restrictions and full multiworld progression spheres. Guarantee viable
early checks and recovery equipment without depending on lucky loot or an item
behind its own requirement. Reject unsupported unsafe starts clearly.

## Checks: required categories and precise proposed triggers

All checks are finite and monotonic. Threshold lists are sorted, unique and capped
at generation time. A repeatable activity never becomes an unlimited check farm.
Keep the three published pilot location IDs and never recycle an ID.

| Proposed option | Trigger and completion rule | Investigation and acceptance |
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

| Proposed option | Reward behaviour | Required constraints |
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

Proposed zone-key travel policy: one optional trip on unlock to one designated
safe settlement in the newly unlocked zone, once other protection/story
requirements are met. Never teleport automatically. For a zone without a viable
hub, offer an already unlocked safe settlement instead. Persist eligibility and
consumption; show the chosen destination. Resolve hostile hubs, unavailable
guides, fees, current fast-travel restrictions and extra-transition mods before
shipping this policy. This is a design proposal requiring playtest validation.

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

The current bridge carries item IDs only. Plan a versioned metadata extension,
with explicit v1 compatibility/migration tests, rather than silently changing
the wire format. Incoming messages occur after successful in-game application;
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

See [branch roadmap](branch-roadmap.md) for the individual PR boundaries. Each
stage can require several small branches. A source hook is a lead until its
callback arguments and save behaviour have been observed in the installed build.

### Stage 0: close the pilot and inventory compatibility

- [x] Third-map trigger and ordinary game save/reload accepted by the user;
  see the verification record for confirmation versus captured evidence.
- [ ] Independently capture the remaining reward and actual goal packet.
- [ ] Verify disconnect/reconnect and wrong-seed refusal in a disposable dev save.
- [ ] Record the exact GAMMA/engine/AP/mod baseline and active MO2 file winners.
- [ ] Classify existing third-party script errors; resolve those affecting a
  planned integration before treating it as supported.
- [ ] Inventory all requested content rosters and real callbacks/info portions.
- [ ] Record credit rules, task identities, equipment tiers and lab roster.
- [ ] Identify authoritative starter grants, faction/difficulty loadouts and PDA
  dependencies before defining supported restricted-start combinations.

Exit: repeatable pilot evidence and a finite manifest/probe backlog; no claim that
current inventory receipts prove crash-safe recovery.

### Stage 1: PDA messages and durable session recovery

- [ ] Preserve sender, recipient, foreign item name and known unlock kind.
- [ ] Implement versioned bridge metadata and PDA incoming/outgoing messages.
- [ ] Verify one correct notice for self-rewards and each confirmed transfer.
- [ ] Define save rollback and notification replay policy; separate permanent
  unlock reconciliation from consumable replacement.
- [ ] Verify AP server restart and game/client restart with persisted state.

Exit: a live two-player or mixed-game test proves both directions and names;
reconnect/load do not spam or create rewards twice because a notice failed.

### Stage 2: options, catalogue and exploration

- [ ] Implement all category options and typed, versioned slot manifest.
- [ ] Add independent starting-loadout omissions and the No Starting Weapons
  preset; initialize once before AP grants and preserve later earned inventory.
- [ ] Add every supported map, preserving pilot IDs.
- [ ] Add every curated major settlement using actual entry volumes.
- [ ] Build a real region graph from current transitions, including extra routes.
- [ ] Verify all-off rejection, each toggle alone, presets and pool sizing.

Exit: all map/settlement checks can be generated and demonstrated, with no checks
leaking from disabled categories and no IDs depending on option order.

### Stage 3: combat, collection, tasks, equipment and rank

- [ ] First mutant species and first stalker faction kills, independently toggled.
- [ ] Finite cumulative kill thresholds with defined credit and deduplication.
- [ ] Artefact types with tested pickup/trade/crafting provenance rules.
- [ ] Quest-type first completions and bounded side-task completion totals.
- [ ] Gear upgrade, armour tier, firearm tier and knife tier milestones.
- [ ] Story milestones and Stalker Rank thresholds.
- [ ] Save all counters/sets; test downgrade, reset, duplicate callback and reload.

Exit: every check category has a fixed roster, engine evidence and corresponding
AP reachability assumptions. Active quests or naturally earned skill gains must
not create unbounded feedback through AP rewards.

### Stage 4: stash, reputation and skill rewards

- [ ] White loot stashes with quality/ammo-family options.
- [ ] Orange progression stashes with guaranteed contents and local claim events.
- [ ] Reputation bonuses with demonstrated trader-tier changes.
- [ ] Skill level rewards through the supported installed stat-mod adapter.
- [ ] Classify every reward as consumable, permanent permission or claimed stash;
  verify the recovery policy separately for each.

Exit: direct grants and stash contents survive save/load under the documented
policy, and disabled categories impose no new locks or missing dependencies.

### Stage 5: quest and zone keys

- [ ] Implement quest-stage permissions and ordinary-source replacement.
- [ ] Add AP-locked starting-equipment permissions and their required unlock
  rewards, including PDA restoration, usable baseline gear and queued messages.
- [ ] Implement zone access permissions across normal, extra, scripted and
  fast-travel routes. Preserve return travel and the starting safe region.
- [ ] Offer and persist one optional settlement trip after a zone unlock.
- [ ] Model protection, trader, stash and story prerequisites in AP logic.
- [ ] Test self-locks, hostile hubs, death, load in a locked area and old saves.
- [ ] Test no-detector, no-PDA and no-weapons starts individually and combined;
  verify early progression, bought/looted gear policy and duplicate starter grants.

Exit: game enforcement matches generator access rules; no progression key is
placed behind itself and every supported configuration has a completion route.

### Stage 6: five goal choices

- [ ] Get Psi Protection.
- [ ] Disable Brain Scorcher.
- [ ] Meet Strelok.
- [ ] Complete Living Legend.
- [ ] Visit all X-Labs in the published roster.
- [ ] Verify exactly one server goal transition after the chosen actual condition.
- [ ] Test every goal against applicable category and gating combinations.

Exit: one fresh successful engine playthrough per supported goal, plus regression
tests for premature completion, disabled related check categories and lost packets.

### Stage 7: balance and release

- [ ] Publish presets, configuration examples and unsupported combinations.
- [ ] Run at least 1,000 deterministic seeds for each supported preset, individual
  option tests, pairwise combinations and targeted goal/gate adversarial seeds.
- [ ] Complete two fresh MVP playthroughs and a real mixed-game multiworld.
- [ ] Test clean install, upgrade/migration, uninstall and save recovery.
- [ ] Measure callback/poll cost and notification bursts on the pinned build.
- [ ] Complete independent playtesting, compatibility, licences and release docs.

Exit: every supported requested category and goal has implementation, tests and
engine evidence; unresolved features are labelled and discussed rather than
advertised as complete. Multiplayer here means Archipelago multiworld; in-world
xrRazom co-op remains a separate investigation and installation.

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
