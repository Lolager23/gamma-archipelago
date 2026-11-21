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
game's `appdata/archipelago`. The client writes the incoming snapshot atomically.
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

An optional live-presence sidecar supplies the authenticated slot name and an
advancing connection heartbeat for startup/reconnect PDA notices. Its transient
game cache owns only presentation; it never enters save, item or check state.
Automatic join/transfer display also shares one transient loading-readiness gate:
native screen dismissal followed by a later unpaused, non-precaching world frame.
This gate never delays or acknowledges item/check state.

The [PDA tracker](pda-tracker.md) reads a detached view from the game-state owner.
The projection groups progression facts by status, unlocked/locked permissions
and exploration without parsing presentation strings; its legacy flat list is
retained. The UI's Checks/Progression pages and native list selection own no
progression state.

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
their captured native methods. The AP world and PDA use matching conservative
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
ammunition calibre is seed configuration. A package receipt grants its contents
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

## State and failure boundaries

[Generation pacing](generation-pacing.md) keeps a pure shared pool budget separate
from upstream item creation and placement. Explicit opening reservations run
before general fill. Zone keys use upstream randomized fill in expanded regional
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
