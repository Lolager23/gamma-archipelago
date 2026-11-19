# Randomisation and product goals

Implementation update: the [PR/status index](implementation-status.md) records the
30-step candidate and remaining engine acceptance. The planning text below is
retained as the original specification and milestone history.

## Design principles

Preserve GAMMA's scavenging and repair loop while making selected progression
depend on the multiworld. Every check must be finite, identifiable and recoverable.
Keep food, basic medicine and practical ammunition available without waiting for
another player. Never require an item placed behind its own unlock. Difficulty
must be an option with defined logic assumptions, not an accidental softlock.

The following is a planned catalogue. It is not a claim that these features have
already been implemented. The [expanded checklist](expansion-plan.md) is the
current specification for the 18 November request: it defines every proposed
APWorld toggle, exact trigger/reward contracts, notification wording, five goals
and staged acceptance. Any feasibility problem with requested scope must remain
visible and be discussed rather than silently dropping the feature.

## Candidate checks

| Candidate | Proposed treatment | Main investigation |
|---|---|---|
| First visit to a region | One check per named region | Distinguish actual arrival from loading/menu state |
| Major settlements | One first-entry check per curated major hub | Stable entry volumes and overlap/load deduplication |
| Selected static stashes | One check per stable stash identity | Avoid dynamic IDs and empty/repopulated duplicates |
| Story tasks | Check on verified completion | Faction variants, task IDs and info portions |
| First artefact of a type | One check per supported artefact | Loot pickup, crafting and transfer provenance |
| Laboratory milestones | Finite exploration/story checks | Entry protection and alternate routes |
| Named unique tasks | Curated one-off list | Cancellation, failure and NPC death |
| Repeatable jobs | Bounded milestones per region/type | Do not create an infinite item farm |
| Mutant kills | Independently toggled first-species checks | Companions, environment kills and reliable attribution |
| Stalker faction kills | Independently toggled first-faction checks | Victim faction at death, nonessential targets and story safety |
| Kill totals | Finite configurable threshold list | Actor credit, victim identity and saved counters |
| Quest types | First successful completion per normalized type | Task-template mapping and terminal state |
| Side-task totals | Finite configurable threshold list | Task-instance identity; exclude failed and story jobs |
| Equipment upgrades | Finite successful-installation milestones | Distinguish actual upgrade work from repair or menu access |
| Armour tiers | Independently toggled light-to-heavy equip milestones | Explicit manifest, not raw weight |
| Weapon classes/tiers | Independently toggled firearm equip milestones | Explicit categories/tiers, not price or calibre alone |
| Knife tiers | Independently toggled better-knife equip milestones | Permanent high-water mark and downgrade deduplication |
| Stalker Rank | Independently toggled monotonic rank thresholds | Active rank mod, rank loss and save/load |

Every requested category is independently selectable in generation. Finite
thresholds and content rosters are part of slot data. Disabling a check category
does not disable observation needed by the selected goal. See the expanded
checklist for the fourteen proposed check options and their precise semantics.

## Candidate received items

| Category | Candidate rewards | Proposed status |
|---|---|---|
| Toolkits | Basic, advanced and expert tools | Core progression candidate |
| Detectors | Selected detector tiers | Progression where artefact checks need them |
| Psi protection | Supported protection/helmet unlock | Story progression candidate; avoid bypasses |
| Workshop access | Repair/crafting permissions | Explore permanent unlock model |
| Equipment licences | Weapon/armour tier permissions | Explore; preserve scavenging rather than hand out every gun |
| Area access | Transition permits or story unlocks | Later, after physical gate enforcement is proven |
| White stash coordinates | Basic and higher-tier loot, with optional ammo families | Requested reward category; finite seeded contents and one claim |
| Orange stash coordinates | Guaranteed progression contents with distinct marker/text | Requested reward category; world logic includes physical claim and access |
| Quest-stage keys | Named persistent story permissions | Requested reward category; enforce real transitions and suppress bypasses |
| Faction reputation | Bounded bonuses unlocking supported trader tiers | Requested reward category; verify eligibility and hostility interactions |
| Character skill levels | Haruka Skill System/GAMMA adapter | Requested reward category; caps, recalculation and compatible-mod checks |
| Zone keys and arrival travel | Persistent zone permission plus one optional settlement trip | Requested reward category; all routes, safe hub, protection and return access |
| Supplies | Medicine, ammo, repair supplies, money | Bounded filler pool |
| Traps | Equipment malfunction, temporary debuff | Optional exploration only; avoid irreversible damage |

The original six reward switches separate white stashes, orange stashes, quest
keys, reputation, stat levels and zone keys. Starting-gear unlocks add a seventh
category for optional AP-locked equipment starts. Toolkits/detectors/protection remain
candidate content for the progression pool. A disabled reward category must not
leave its AP-specific locks active. Orange markers never substitute for logic
that requires the contained progression item to be physically collected.

## Optional restricted starts

Plan independent starting-loadout options for no detector, no PDA, no firearms,
no knife/melee, no outfit/headgear, no backpack, no tools and optional reductions
to utility equipment, ammunition, supplies and money. Defaults preserve the
ordinary loadout. The No Starting Weapons preset omits firearms and melee;
No Starting Firearms can preserve the knife.

Separate initial omission from a durable AP permission lock. Omitted gear can be
found normally; AP-locked gear requires a matching unlock reward and documented
usable baseline equipment. Consumables use quantity/omission settings. Generation
validates early access, enabled reward categories, pool size and protection needs.
No-PDA starts keep the AP client/bridge working and queue PDA-only messages until
restoration. Initialize only once, before AP rewards; never strip earned gear on
reload. The expanded checklist specifies the full contract and acceptance cases.

## Goal choices and messages

Implement Get Psi Protection, Disable Brain Scorcher, Meet Strelok, Living Legend
and Visit all X-Labs as separate choices, with explicit actual completion states.
Keep the three-region tour as a development goal. The exact lab roster and
qualifying psi-protection variants are inventory tasks, not assumptions. Each
goal needs a valid route under the chosen reward/category options and start.

Add PDA messages for applied incoming rewards and confirmed outgoing transfers,
including player and item/unlock names. Use "gave you" for physical items and
"unlocked your" for known permissions; self-rewards produce one message. The
expanded checklist specifies metadata, foreign-game names, deduplication and
offline reconstruction. Messages are planned; the current pilot only logs grants.

## Initial pilot, before MVP

Use Cordon, Garbage and Rostok arrival as three deterministic checks. Randomise a
basic toolkit, a medkit and a bandage. Completing all pilot visits is the pilot
goal. No progression blocking, story replacement, stash overhaul or multiplayer
support is promised by this small transport test. Start a new development game.

## MVP acceptance

- Loner start in Cordon, single-player, one documented difficulty baseline.
- Approximately 30–50 curated checks across a small, connected southern route
  and the selected story route; exact count follows the callback investigation.
- A small meaningful progression pool: toolkits and the protection/detector
  unlocks actually needed by those checks.
- One complete goal, initially disabling the Brain Scorcher if its task and
  access conditions prove reliable; otherwise choose and document an earlier
  complete story goal before implementing the final rules.
- Suppress or replace the normal acquisition routes for shuffled progression
  items. Receiving equivalent loot must not silently bypass the randomiser.
- Generator access rules and game enforcement agree, including alternate routes.
- The player can send checks offline, reconnect, receive queued items and reload
  saves under the documented recovery rules.
- New saves bind to a single seed/slot; mismatch produces a useful error.
- 1,000 deterministic generation tests, targeted adversarial seeds, a real mixed
  multiworld and two fresh complete in-game playthroughs.
- Required coverage and CI gates pass; no open progression-loss or save-corruption
  defects. Installation, setup, recovery and removal are documented.

The 30–50 check MVP remains the first complete playable slice. It is not the final
expanded scope: every requested category and all five goal choices are tracked
through the staged checklist and release acceptance, with individual generation
options and verified integration requirements.

## Exploratory stretch goals

- Full Zone transition randomisation with reachability and return-route logic.
- Additional faction/start variants and story chains beyond the tested presets.
- Unique weapons and repair/equipment licences beyond the requested rewards.
- DeathLink with explicit consent and rules for load/death loops.
- Reversible traps such as short debuffs or an announced emission; investigate
  whether quest-critical NPCs and recoverable saves can remain protected.
- A full PDA dashboard for connection state, item history and missing checks,
  beyond the requested incoming/outgoing reward messages.
- xrRazom co-op: explicit shared-slot versus separate-slot design, host authority,
  reward ownership, join-in-progress and save recovery. Never assume that normal
  Archipelago multiworld support implies in-world co-op compatibility.
- Additional goals beyond the five requested choices, such as Miracle Machine.

Each stretch feature needs a standalone feasibility result and branch. A negative
result is useful; it can remove a feature from scope.

## Finished-product acceptance

Finish the requested expanded scope tracked in the checklist; treat any proposed
deferral explicitly. Additional stretch ideas remain separate. Freeze and
document item/location IDs; provide schema migrations or a clear breaking-change
policy. Ship a reproducible `.apworld`, MO2 add-on and companion client with
versioned compatibility, checksums and licence notices. Verify clean installation,
upgrade, disable and removal. Complete independent playtesting and a supported
multiworld run, performance checks and recovery documentation. Maintain a known
issues list and ownership for subsequent compatibility updates.
