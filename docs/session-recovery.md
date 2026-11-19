# Step 04: session recovery

Stack base: PDA message PR #7. Server-confirmed checks are published in an
optional, independently versioned `confirmed_checks.txt` snapshot. The game
validates its session and full contents before applying it. Accepted checks are
merged monotonically into save state: loading an older save cannot silently
forget already-confirmed visits or prevent the pilot goal after all visits.
Older companions without this sidecar remain compatible.

The companion scouts only its server-confirmed checked locations, at most 64 per
request, without creating hints. LocationInfo supplies the actual item and
recipient for outgoing-notice reconstruction. Unchecked scouts do not announce
transfers. Unknown item names wait for the relevant data package. Notice IDs
remain stable, so a loaded save's displayed-ID set suppresses duplicate notices.
Scouting requests reset on reconnect; item and check histories remain validated.

Recovery policy:

- The AP server is authoritative for completed checks and ordered rewards.
- The loaded game save is authoritative for physical inventory and applied
  receipt count. Missing consumable receipts replay one per update after an older
  save loads, restoring the history missing from that save.
- Ordinary reload retains displayed notices. Loading an older save may replay
  notices absent from that older saved PDA history, consistent with replayed
  rewards. Do not describe rollback as exactly-once delivery.
- A failed notice cannot reapply an item. A malformed or foreign confirmed-check
  snapshot cannot mutate checks or trigger new reward application.
- Future permanent permissions and stash claims need their own idempotent
  adapters; they cannot be treated as repeated consumable grants.

Actual solo/APQuest server tests now construct a fresh client after restoring
the server's on-disk state. It recovers all three items/checks, goal status and
outgoing notice identities through the actual network protocol. Lua tests verify
an older save recovers confirmed visits, validates sidecars and still refuses
forbidden write paths. Local verification passes 243 covered tests plus two real
server cases, with 100% measured owned Python line/branch and Lua executable-line
coverage. Lua branch coverage is not measured.

Engine crash timing, a live wrong-seed attempt, physical older-save recovery and
permanent/stash reward recovery remain acceptance cases. Automated synthetic game
snapshots do not close those engine tests. Do not deploy into an active game;
back up the full isolated appdata/profile/overwrite/configuration first.
