# Step 03: PDA reward messages

Stack base: Step 02 / PR #6. The companion now preserves player and item names
and sends optional notice snapshots to the game's PDA news API. Examples:

- `Friend gave you a Basic Toolkit`
- `Friend unlocked your Zone Access` for an explicitly known unlock effect
- `You gave Friend Moon Key` for a confirmed outgoing transfer
- `You unlocked Friend's Zone Access` for a known outgoing GAMMA unlock

Physical and unknown foreign-game items use "gave". Foreign progression flags
do not imply an equipment permission. Known GAMMA unlock effects are explicit
catalogue metadata; the three current pilot rewards are physical items.

Incoming notices are keyed by receipt index and wait for the save's applied-item
count. Outgoing notices are keyed by source location, recipient and item, and
come from a real server ItemSend confirmation. Self-awards only show the incoming
notice. Notices never create inventory objects. A PDA display failure cannot
repeat item application; successful display identities are saved separately.

The v1 item bridge remains compatible. Optional sidecars use their own version:
`notices.txt` is atomically published by the companion and `notices_ack.txt` is
written by the game. Every snapshot binds to the same session key. Each batch
contains at most 16 notices; the game displays at most one each normal poll.
Malformed, oversized, wrong-session and unsafe-text messages are refused.
Acknowledgements from an older seed cannot suppress this seed's messages.

Player/item labels retain printable Unicode and remove control/formatting text;
names are bounded. UTF-8 text is hex encoded across the ASCII sidecar. The game
uses `give_game_news` with the Archipelago header. Actual fonts, history visibility
and sound remain live acceptance, separate from mocked news-API tests.

Ordinary save/reload retains displayed IDs, including migration from existing v1
saves without the new field. Incoming metadata is reconstructed from item history
after reconnect. Reconstructing outgoing notices after client-process restart or
offline play is the next recovery increment; transient ItemSend packets alone
are not a durable journal. Future no-PDA permission gates must defer display
without preventing bridge progress.

Full verification passes 227 covered tests and two real-server cases. Owned
Python line/branch coverage and all owned non-generated Lua executable-line
coverage are 100%; Lua branch coverage is not measured. Tests include failure,
malformed data, safe names, wrong seed, batching, receipt boundaries, duplicate
self/transfers and saved notice replay. The server fixture now actually uses
APQuest: an earlier fixture used the empty Archipelago meta-world. The current
test proves real cross-game transfers and outgoing notices, as well as persisted
server restart. The separate generation test already used APQuest correctly.

No new map/reward category or goal is enabled by this PR. Deployment and actual
PDA visual acceptance must be recorded separately; do not infer them from tests.

## Protocol ID compatibility

Foreign item IDs use Archipelago 0.6.8's signed 53-bit range
(`-9007199254740991` through `9007199254740991`). Notice identities and
acknowledgements preserve their canonical decimal strings in Lua, so large IDs
cannot be rounded into another transfer. Negative zero, leading zeros and values
outside that range are rejected. This fixes the earlier ten-digit restriction;
local GAMMA location IDs and receipt bounds remain unchanged.
