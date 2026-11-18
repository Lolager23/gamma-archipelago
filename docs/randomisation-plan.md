# Randomisation and product goals

## Design principles

Preserve GAMMA's scavenging and repair loop while making selected progression
depend on the multiworld. Every check must be finite, identifiable and recoverable.
Keep food, basic medicine and practical ammunition available without waiting for
another player. Never require an item placed behind its own unlock. Difficulty
must be an option with defined logic assumptions, not an accidental softlock.

The following is a planned catalogue. It is not a claim that these features have
already been implemented or that every candidate will survive investigation.

## Candidate checks

| Candidate | Proposed treatment | Main investigation |
|---|---|---|
| First visit to a region | One check per named region | Distinguish actual arrival from loading/menu state |
| Selected static stashes | One check per stable stash identity | Avoid dynamic IDs and empty/repopulated duplicates |
| Story tasks | Check on verified completion | Faction variants, task IDs and info portions |
| First artefact of a type | One check per supported artefact | Loot pickup, crafting and transfer provenance |
| Laboratory milestones | Finite exploration/story checks | Entry protection and alternate routes |
| Named unique tasks | Curated one-off list | Cancellation, failure and NPC death |
| Repeatable jobs | Bounded milestones per region/type | Do not create an infinite item farm |
| Mutant kills | Optional first-species milestones | Companions, environment kills and reliable attribution |
| Rank/reputation thresholds | Optional monotonic checks | Faction changes and reputation loss |
| Crafting/repair milestones | Optional first completion | Detect real work rather than receiving the result |

## Candidate received items

| Category | Candidate rewards | Proposed status |
|---|---|---|
| Toolkits | Basic, advanced and expert tools | Core progression candidate |
| Detectors | Selected detector tiers | Progression where artefact checks need them |
| Psi protection | Supported protection/helmet unlock | Story progression candidate; avoid bypasses |
| Workshop access | Repair/crafting permissions | Explore permanent unlock model |
| Equipment licences | Weapon/armour tier permissions | Explore; preserve scavenging rather than hand out every gun |
| Area access | Transition permits or story unlocks | Later, after physical gate enforcement is proven |
| Supplies | Medicine, ammo, repair supplies, money | Bounded filler pool |
| Traps | Equipment malfunction, temporary debuff | Optional exploration only; avoid irreversible damage |

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

## Exploratory stretch goals

- Full Zone transition randomisation with reachability and return-route logic.
- Multiple factions and alternative story chains, including hostile starts.
- A curated artefact catalogue, unique weapons and repair/equipment licences.
- Optional bounded job, hunting, crafting and reputation check sets.
- DeathLink with explicit consent and rules for load/death loops.
- Reversible traps such as short debuffs or an announced emission; investigate
  whether quest-critical NPCs and recoverable saves can remain protected.
- A PDA page for connection state, received items and missing checks.
- xrRazom co-op: explicit shared-slot versus separate-slot design, host authority,
  reward ownership, join-in-progress and save recovery. Never assume that normal
  Archipelago multiworld support implies in-world co-op compatibility.
- Additional goals such as Miracle Machine, story completion or a curated tour.

Each stretch feature needs a standalone feasibility result and branch. A negative
result is useful; it can remove a feature from scope.

## Finished-product acceptance

Finish the chosen supported scope rather than every stretch idea. Freeze and
document item/location IDs; provide schema migrations or a clear breaking-change
policy. Ship a reproducible `.apworld`, MO2 add-on and companion client with
versioned compatibility, checksums and licence notices. Verify clean installation,
upgrade, disable and removal. Complete independent playtesting and a supported
multiworld run, performance checks and recovery documentation. Maintain a known
issues list and ownership for subsequent compatibility updates.
