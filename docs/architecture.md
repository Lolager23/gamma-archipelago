# Architecture

## Responsibilities

There are three required components, each with one owner:

1. **AP world:** Python definitions for items, locations, generation rules, options
   and completion conditions. It does not modify a running game.
2. **Companion client:** a single process owns the connection, seed/slot identity,
   validated item history and communication with the game. Networking uses
   Archipelago's `CommonClient`; we do not reimplement its websocket stack.
3. **Game add-on:** Lua callbacks observe supported milestones, create approved
   reward sections and save the game's receipt state. They never use the network.

Communication is a versioned pair of plain-data snapshots under the isolated
game's selected appdata `archipelago` directory. The client writes the incoming snapshot atomically.
The game writes its own outgoing snapshot. Each file has one writer. A central
coordinator handles validation and reconciliation; no event bus or distributed
service layer is needed.

Optional PDA notices carry semantic transfer fields; the game adapter renders
whole-sentence string-table templates in the selected language with English
fallback. This presentation channel owns no item-application state. Version 3
adds source-check causes while reading versions 1/2 and retaining version-1
acknowledgement/save identities. A pure catalogue projection describes GAMMA
checks; the CommonClient notice adapter resolves the finder slot's game and
data-package metadata. The game translates the sentence, cause and owned value.
See [PDA messages](pda-reward-messages.md) for coordinated bundle upgrades.

Optional room news and connection diagnostics are presentation channels.
The companion writes bounded session/configuration-bound room/status snapshots;
the game writes a bounded challenge-bound request queue for chat and hints.
A first ready-world entry requests room chat once per game process, with request
submission deduplication across companion reconnects. Level/save loading never
resets that queue, including when Lua modules are reconstructed. The small
`game_run` adapter derives the process token from the native log start marker and
keeps presentation counters in isolated appdata. The room cursor also survives
Lua reloads; the existing notice acknowledgement file suppresses already-displayed
notices when loading an older save. These caches never apply receipts.
Upstream Join/Part retains its real connection meaning.
The legacy presence heartbeat remains available to older bundles; the current
add-on no longer emits a local join popup from it. None of these caches owns
checks, received history or applied receipt state. See [PDA messages](pda-reward-messages.md).
Automatic room/transfer display and world-entry requests share one transient
loading-readiness gate: native screen dismissal followed by a later unpaused,
non-precaching world frame. The same gate protects weather observations and
optional stamina restoration. It does not acknowledge items or delay receipt
application. A user-requested MCM diagnostic can print while the menu is paused.

The [PDA tracker](pda-tracker.md) reads a detached view from the game-state owner.
Settlement diplomacy uses catalogue-backed solver requirements and a read-only
AP receipt projection for tracker availability. Physical settlement entry is
independent of reputation; safe placement assumptions never veto observed entry.
The engine registry still owns goodwill; the AP save
owns applied receipt history. No additional persistent reputation owner exists.
The optional [shared-goodwill conversion](shared-goodwill.md) keeps its absolute
backfill targets in that same save owner, without changing server receipt IDs.
The projection groups progression facts by status, unlocked/locked permissions
and exploration without parsing presentation strings; its legacy flat list is
retained. The UI's Checks/Progression pages and native list selection own no
progression state.

Fresh [equipment classes](equipment-classes.md) derive cumulative use tiers from
starting settings and applied receipt history. Free initial supplies reuse the
central loadout plan, and backpack receipts reuse ordered delivery plans. Native
creation-list filtering constructs permitted section/price pairs before mutation.
No additional persistent class owner or counter exists.

The [regional story rules](regional-story-balance.md) declare equipment/tool
readiness for story events and late equipment checks, plus recipe access for
later artefact discoveries. The APWorld and PDA project the same catalogue rules.
Generic mutant availability uses a pure, bounded region/type matching function;
native observations remain distinct facts owned by the central save. Artefact
rewards reuse ordered delivery plans rather than adding another receipt owner.

Starting equipment permissions gate equip/use, not ownership. The game adapter
keeps acquired gear in inventory, guards native UI/device/input entry points and
reconciles the finite supported equipment slots back to the rucksack. All hooks
read the coordinator's saved permissions through an explicit getter; their local
state contains wrapper identities and warning timing only. Carried-gear upgrades
remain available under the separate tool/workshop rules. The passive calibrated
psi device retains its independent progression-stash acquisition safeguard.
Generated catalogue metadata and a stateless requirement projection supply its
regional/status pages. The UI owns only filters and page offsets; it cannot mark
checks or acknowledge rewards. Its native tab wrapper delegates all other sections
and uses DXML to extend the existing profile layout. No network work runs in UI
refresh or the game update loop.

The PDA Chat & hints composer owns only a transient input draft and feedback.
It delegates unchanged player text to the existing bounded game request queue;
the companion submits upstream Say, and server echoes/replies populate the
existing room feed. Explicit submission and the visible page can flush bounded
request snapshots without waiting for actor updates; they never create the
automatic world-entry request. Outbound punctuation is data, while incoming PDA presentation
retains its separate markup sanitization. Neither chat nor hints owns progression,
checks, item receipts or an independent connection. No native console hook is used.

Optional [scouting](scouting-and-services.md) uses separate bounded request and
metadata snapshots. The save owns request IDs; the companion owns server-sourced
item/recipient metadata and its heartbeat. This channel cannot apply receipts or
complete checks. Shop and standing callbacks delegate to a finite service-check
module and mutate only the central game state.

[Buyable shop contracts](shop-purchases.md) are a separate optional category.
The native trader page reads a copied offer view. Its purchase callback delegates
to the coordinator, which checks bridge identity/history and server confirmations
before the shop adapter spends money. The same save owns paid checks and bounded
uncertain payment intents; no physical tokens or independent shop ledger exists.

[Discovery quotas](discovery-quotas.md) select fixed milestone IDs from catalogue
rosters. The world/client share a pure configured selection; the game adapter
persists only distinct source IDs in central save state. Generated Lua metadata
keeps selection and observation mappings aligned with published IDs.

[Progressive tools](progressive-tools.md) derive their tier directly from applied
receipts. Native workshop wrappers receive an explicit state getter, validate the
supported entry points before installation, and delegate permitted actions to
their captured native methods. Fresh [tool permissions](tool-use-permissions.md)
read the central save's unlocks, deliver one kit through the existing receipt
plan, and allow ordinary acquisition without granting use. Local capability
events express the same contiguous tool tiers to the solver and paced analysis.
The AP world and PDA use matching conservative
upgrade requirements; physical supplies remain owned by the ordinary game.

[Workshop and recipe access](workshop-access.md) extend the same explicit guards
with catalogue-backed permanent permissions. They use the existing saved unlock
set. Recipe groups map to the supported native recipe toolkit indices; native
knowledge and component checks remain the captured method's responsibility.

[Permission supplies](permission-supplies.md) use bounded per-receipt action plans
inside the same save state. Catalogue-defined contents and the ordered applied
history determine each plan. The adapter owns spawning; the tracker reads copied
status. Permanent permission acknowledgement waits for plan completion, and an
uncertain spawn blocks automatic retry. This does not create an engine/save
transaction or change the server's authority over item history.

[Supply packages](supply-packages.md) reuse those plans for repeatable useful
rewards. Their contents and relative optional-pool weights are catalogue data;
ammunition snapshots compatible full-quality types from equipped weapons; legacy plans retain their seed calibre. A package receipt grants its contents
without a permanent permission, while receipt ordering and completion still
belong to the same central save coordinator.

Stash plans also remain in the central save state. Their adapter fills a recorded
box synchronously during its use callback, before GAMMA's loot UI refresh, with
a bounded action budget and the existing timed retry path. Created identities
prevent automatic replacement; uncertain creation still requires manual recovery.
Physical opening does not require a PDA; the coordinate plan and exact container
remain authoritative. Opening is separate from claiming in the tracker. The two AP marker kinds share
an owned, reproducibly generated rainbow texture and retain distinct text hints.

[Convenience carry rewards](convenience-rewards.md) derive their bounded effect
from applied receipts and reconcile one namespaced entry through the active GAMMA
weight API. Their local cache tracks engine application only; it does not own
progression or replace the native modifier system.

[Regional activity logic](regional-activity-logic.md) supplies catalogue-backed source
regions and cumulative story routes to both the AP world and PDA. Distinct quotas
count supported non-excluded source types; uncertain sources and excess quotas
remain optional filler checks and are excluded before progression budgeting.

[Quest-restricted travel](quest-zone-logic.md) shares catalogue-backed northern
gates between the world and PDA. Local AP shutdown events model achievable native
quests without consuming network slots. The game reads the real info portions;
neither the tracker nor a received zone key grants quest completion. Sparse key
planning queries the same access graph rather than maintaining a second route model.

## State and failure boundaries

[Generation pacing](generation-pacing.md) keeps a pure shared pool budget separate
from upstream item creation and placement. Explicit opening reservations run
before general fill. Equipment and workshop access share the early reward
categories and reachable-opening allocation; their native permissions and
delivery state remain separate. Fresh regional recipe permissions use the same paced-analysis
primitives to plan a conservative three-step opening against known rewards.
The plan is validated before placements are committed; no additional saved state
or runtime owner is introduced. Zone keys use upstream randomized fill in expanded regional
pools, including multiworlds, optionally requesting one early hub key. Only sparse
exploration pools retain an anti-cycle route. Optional actual-seed reports are generated after fill;
settings previews contain no placements. Common AP constraints and starting items
use a canonical generation identity in slot schema 4, while legacy schemas keep
their original session keys.

The AP server owns completed location checks and the ordered item history. The
client holds a validated mirror for replay; the save owns the last item actually
applied in that saved game. The bridge includes a unique seed/slot session key.
A save must never attach silently to a different key.

Configured outgoing snapshots also carry the exact settings digest. The companion
requires that digest before accepting checks, receipts or victory, including when
the same seed name/team/slot is reused with different options. See the
[bridge protocol](bridge-protocol.md) for the wire formats and bundle upgrades.

Keep received items pending until the game can apply them. A successful file write
does not mean an item has been applied. An item batch with a gap is rejected and
requires resynchronisation. Duplicate history with different contents is an error.
Location checks are monotonic and can be resent safely.

Anomaly does not provide a general transaction across spawning an item and saving
the game. The initial foundation records acknowledgements in save state and tests
rollback/replay. It must not claim crash-proof exactly-once delivery. The durable
recovery milestone will define permanent unlock reconciliation separately from
consumable replacement, with measured crash and rollback tests before MVP.

## File layout

```text
apworld/gamma/                 Archipelago extension package
src/gamma_archipelago/catalog.json  Stable IDs and supported pilot content
src/gamma_archipelago/         Typed client, bridge and session logic
mod/gamedata/scripts/          Thin callbacks and Lua state/protocol modules
tests/unit/                    Python behaviour tests
tests/lua/                     Lua adapter and state tests
tests/integration/             Real AP generation/server checks
tools/                         Verify, build, deploy and environment checks
web/generator/                 Buildless local seed workbench UI
docs/                          Decisions, workflow and test evidence
```

The catalogue is the source of truth. The build emits a Lua table and checks the
world/client against the same data. Published IDs are never recycled.

The optional [seed workbench](generator-web-app.md) reuses core configuration and
catalogue projections. `web_estimates` owns explicitly provisional time estimates;
`web_generation` owns bounded upstream subprocess execution; `web_server` owns
loopback HTTP. The browser owns its draft form only. These modules do not alter
session/save ownership or access the game bridge. Generated sessions remain in a
separate tooling directory, and no generation request launches the game.

## Isolation boundary

All deploy and client commands validate the development roots. Original game and
MO2 folders are read-only references for this task. Neither installation shares
mods, `overwrite`, appdata, downloads, engine files or an AP state folder. No
hardlinks, symbolic links or junctions join them. Game processes are tested one at
a time. Source files may be edited while the normal multiplayer game is running.

## Player-selected installation paths

The packaged connection launcher accepts the Anomaly folder or portable MO2 folder,
resolves the installed appdata alias and stores the explicit local choice in
`installation.json`. Setup confirms that choice before writing a small enrollment
marker. The client receives explicit game/appdata arguments; the adapter uses the
engine's active `$app_data_root$` and requires that marker outside the legacy DEV
root. No running-game directory is guessed from processes. Process inspection
only prevents overlapping companion writers and configuring a live game.

Enrollment is static installation metadata, not AP check/receipt state. The
existing coordinator and file bridge still own protocol validation and progression.
Published IDs, seed/slot identity and save schemas are unchanged. Both Python and
Lua validate their selected paths; Python refuses links, aliases/escapes and
hardlinked bridge files. Owen's DEV defaults and protected normal installation
remain unchanged. See [portable installations](portable-installations.md).
