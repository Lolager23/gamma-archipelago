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
fallback. This presentation channel owns no item-application state. Its version 2
sidecar retains version 1 acknowledgement/save identities and accepts old text
sidecars. See [PDA messages](pda-reward-messages.md) for coordinated bundle upgrades.

The [PDA tracker](pda-tracker.md) reads a detached view from the game-state owner.
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

[Discovery quotas](discovery-quotas.md) select fixed milestone IDs from catalogue
rosters. The world/client share a pure configured selection; the game adapter
persists only distinct source IDs in central save state. Generated Lua metadata
keeps selection and observation mappings aligned with published IDs.

## State and failure boundaries

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
