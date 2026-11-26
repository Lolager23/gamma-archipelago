# Game snapshot configuration binding

Configured slot schemas 2, 3 and 4 require outgoing protocol 3. The companion binds
the expected digest from validated slot data before polling the game. Both the
session identity and settings digest must match before accepting any observation.
Reusing a seed name/team/slot with different options cannot import an old file.

```text
GAMMA_AP_OUT|3
session|<64 lowercase hexadecimal characters>
configuration|<64 lowercase hexadecimal settings digest>
received|<canonical nonnegative receipt count>
check|<enabled location ID>
goal|0
end|<number of check records>
```

The check record repeats zero or more times. The selected goal controls victory
validation; its identity is included in the settings digest. Existing bounds,
canonical numbers, record ordering, check manifests and receipt checks still apply.

Legacy unconfigured pilot slots use protocol 1. Earlier unbound alternate-goal
protocol 2 remains a parser compatibility format; configured slots require the
bound format. Upgrade the companion and add-on together: old outgoing files are
refused until the updated game adapter writes protocol 3. Saved receipt and check
state does not change. A configured save refuses an unbound legacy companion;
restore its matching configuration instead of silently dropping the settings lock.

Slot schema 4 additionally carries a 64-character lowercase SHA-256
`generation_identity` for non-default common AP constraints or precollected items.
The session key hashes `seed_name + "|generation|" + generation_identity`, team and
slot through the existing key function. This binds starting gifts/from-pool,
local/non-local, exclusions and plando settings without changing outgoing/save
formats. Schema 1–3 session keys remain unchanged. A schema-4 identity on an older
schema, malformed identity or reconnect with a changed key is refused. Older
companions reject schema 4; use a matching bundle and fresh seed for new settings.


## Optional room communication, version 1

These sidecars require the matching companion/add-on bundle and are independent
of check, item and save protocols. They never grant rewards or acknowledge items.
All filenames are fixed under the validated enrolled bridge root. The companion
atomically replaces its snapshots; incomplete game-owned requests are refused.

`room_feed.txt` contains `GAMMA_AP_ROOM|1`, session, configuration (or `-`),
`heartbeat|<16 lowercase hex epoch>|<counter>`, then at most 64
`message|<increasing counter>|<UTF-8 hex text>` records and `end|<count>`.
Counters are canonical decimals up to 999999999. Each message is at most 2048
UTF-8 bytes, with controls/PDA markup removed; the snapshot is at most 280000
bytes. The transient game cursor is not a saved notice identity. It waits for an
observed heartbeat advance and a ready world; static files cannot initiate news.

`connection_status.txt` has exactly these records:

```text
GAMMA_AP_STATUS|1
session|<session key>
configuration|<configuration digest or ->
heartbeat|<companion room epoch>|<counter>
connection|<0 or 1>|<UTF-8 hex credential-free server label>
ack|<game process epoch or ->|<last submitted request counter>
confirmed|<server-confirmed check count>
hint|<points>|<cost percent>|<total locations>
end|1
```

The snapshot is at most 8192 bytes. The game computes its backlog by set difference
against the exact validated `confirmed_checks.txt` IDs, not by subtracting this
summary count. It reports unknown when confirmations cannot be validated. An
advancing status heartbeat can truthfully report a disconnected AP socket;
a stale heartbeat cannot prove an online server.

`game_requests.txt` contains `GAMMA_AP_COMMANDS|1`, session, configuration,
`game|<16 lowercase hex process epoch>`, `target|<current companion room epoch>`,
at most 32 `request|<counter>|<loaded or say>|<UTF-8 hex text>` records and
`end|<count>`. It is at most 40000 ASCII bytes. `loaded` has an empty payload;
`say` has 1-512 safe UTF-8 bytes. Requests are ordered and deduplicated within the
companion process. A new companion accepts the first pending counter as its
restart boundary; thereafter gaps cannot advance the acknowledgement. Old target
challenges are ignored. A different saved session drops the transient game queue.

The game queues `loaded` after its first ready-world load, without resetting on
level/save changes. The companion supplies the authenticated slot name and sends
ordinary AP Say chat. The same queue carries explicit player hint requests as
`!hint`/`!hint <item name>`. Text is never evaluated as Lua/Python or as an engine
command. The AP server interprets its own chat commands. The websocket submission
acknowledgement is not an end-to-end or crash-proof chat delivery guarantee.
