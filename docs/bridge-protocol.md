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
