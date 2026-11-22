# Regional activity logic

This increment replaces the all-zones activity gate with catalogue-backed regional
opportunities and the existing equipment/quest permissions. It changes generation
and the PDA projection, not the engine observation callbacks or saved receipts.
Native acceptance is **not run**, reserved for Owen. Existing seed archives are
never refilled. No installed game or running session is changed by this PR.

## Requirements and ownership

`src/gamma_archipelago/catalog.json` owns the curated region alternatives and
cumulative story routes. `activity_requirements` projects them into immutable
requirements for the world and pool budget. The build emits the equivalent Lua
metadata; the stateless `gamma_ap_activity` projection supplies PDA availability.
Regions retain their normal adjacency, zone-key and usable-psi requirements.

- Per-type mutant/faction kills require one supported source region and a weapon
  permission if both firearm/melee groups are AP locked. Combat-readiness options
  retain their additional firearm/armour requirements.
- Artefacts require a supported anomaly region plus Detector permission when locked.
  Owning a detector in inventory does not bypass its equip/use permission.
- Quest types and side tasks require PDA permission when locked. Combat task types
  also require combat capability. Supported fetch/assault/territory tasks can be
  done from Cordon; the supported named hunting opportunity also requires Meadow.
- Upgrades require a reachable technician area, Tools use permission when locked,
  and independent progressive-tool/workshop access. Stored guns/armour need no
  firearm/outfit equip permission merely to be upgraded.
- Novice rank (threshold zero) is a free baseline check in every starting region.
  Later rank/standing checks require a repeatable earning route: PDA tasks or usable weapons.
  They cannot bootstrap their own only PDA/weapon permission from a fully locked start.
- Story checks use cumulative native chain destinations, not every map. From
  Breakthrough onward they retain the preceding mandatory combat capability;
  Mortal Sin/Afterglow cannot hold the only weapon permission needed to finish
  Living Legend. Local Strelok/victory events reuse the same story requirements. Living
  Legend's terminal goal uses its chain route rather than unrelated maps. Existing
  story quest-key requirements remain. No artificial early/middle/late item tiers
  or category placement quotas are added.

Required progression still uses upstream randomized fill, common constraints and
configured opening reservations. If no reliable activity is initially usable,
but one pending PDA/detector/firearm/melee permission would open one, the world
requests one such permission through upstream `early_items`. The seeded choice
is earned at an eligible early check; it is not a starting gift or fixed-location
placement. Existing user early requests and precollected/protected openings are
respected. This minimal safeguard also applies to legacy/challenge opening mode:
the 1,000-seed regression found a dependent-tools clog otherwise. Full protected
opening remains a separate, stronger policy. A sparse map/story-only pool with no reliable
non-map opening opportunity retains the anti-cycle fallback. A distant story
check cannot provide the initial slack needed by that pool; this failure is a
regression case. Full Story uses general fill.

## Distinct quotas and uncertain sources

A generic Nth discovery requires N distinct supported types with reachable source
regions, after configured exclusions. Repeated kills/pickups do not increase that
source count. Opening a map does not count as discovering a type. Configured final
filler tails remain independently enforced.

The inspected baseline supplies supported regional opportunities for 20 of 25
mutant types and 60 of 66 artefact types. Five mutant types (Bibliotekar, Borya,
Giant Jumper, Rat, Zombie), six artefacts (Atom, Compass, Death Lamp, Fountain,
Monolith, Oasis Heart), unsupported task routes and story-dependent Sin/UNISG
kill targets are retained as optional checks but excluded from progression and
useful placements. This is an evidence limit, not a claim they never spawn.
The missable-check option does not override these unsupported-source exclusions.

Generic quotas beyond the supported non-excluded roster are also filler-only.
Their PDA projection waits for the supported roster and labels the unresolved
remainder optional; it does not assert those missing types are obtainable. A
logical all-check reachability result therefore does not prove every optional
native encounter exists. Native source support can be extended separately with
evidence. Generation budgets reserve required items before optional rewards and
account for all of these exclusions; insufficient reliable capacity is rejected.

## Source evidence and practical limits

The region lists were derived from Anomaly 1.5.3 configuration and the active
Archipelago DEV profile's loose GAMMA overrides, including:

- G.A.M.M.A. NPC Spawns: `configs/scripts/*/smart/*.ltx`, selected respawn groups,
  day-zero/unconditional branches, `misc/squad_descr/squad_descr_default_mutants.ltx`.
- Native `misc/simulation.ltx` initial occupants and creature inheritance. Species
  follow the adapter's kind-first mapping; Lurkers are not counted as Chimeras merely
  because they share the underlying engine class. Week-gated groups are not used
  to promise opening diversity.
- G.A.M.M.A. Artefacts Reinvention: `items/settings/artefacts.ltx` groups and actual
  `scripts/*/anomaly/*anomal_zone.ltx` references. Merely appearing in a group list
  does not establish that a field actually uses that group.
- G.A.M.M.A. Quests Rebalance: `misc/task/tm_escape.ltx`, other named task files,
  and `tm_lostzone_ll/ms/oa.ltx` target/condition routes. Unsupported dynamic target
  selection remains optional instead of promising a random destination is unlocked.

Private source inventories/hashes remain outside Git; no game assets are packaged.
These are access opportunities, not guarantees of a particular encounter on demand,
weather cycle, surviving NPC, item condition, trader stock or completion time.
ALife, story branches and equipment availability require Owen's playtests.

Primary references: [GAMMA source](https://github.com/Grokitach/Stalker_GAMMA),
[pinned AP world API](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/docs/world%20api.md),
[pinned AP fill](https://github.com/ArchipelagoMW/Archipelago/blob/54803be064fc7e80c4628777ed0b46a9390f255f/Fill.py).

## Verification and native acceptance

Regressions compare generated Python and Lua requirements for every catalogue
entry, quota/exclusion outcomes and several region sets. Full Story AP/PDA checks
are compared under locked starts, partial keys, permissions and psi states. Tests
cover early boar/artefact/fetch checks, equipment self-locks, source ceilings,
uncertain-source filler protection, sparse story openings and filled seed spheres.
Complete verification and exact-head CI evidence belong to the PR record.

Owen should verify early source encounters, artefact collection with permission,
repeatable task routes, distinct quota ordering, PDA explanations, story route
milestones, incoming rewards and save/reload in a newly generated Dev session.
No game is launched automatically. Older archives keep their original placements;
a coordinated world/client/mod upgrade and fresh seed is required for new logic.
