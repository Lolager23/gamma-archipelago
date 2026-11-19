# PDA reward messages

The companion preserves player and item labels and publishes optional notices to
the game's news API. Archipelago broadcasts appear without owning a PDA,
including when the starting PDA is omitted or AP-locked. English examples:

- `Friend gave you "Basic Toolkit".`
- `Friend unlocked your "Zone Access".`
- `You sent "100 Rupees" to James.`
- `You unlocked "Zone Access" for James.`
- `GammaPilot joined the Archipelago.`

Quoted item labels work with plurals, currency, acronyms and foreign-game names
without guessing an English article. Outgoing messages avoid possessive-name
rules. Only explicitly known GAMMA unlock and skill effects use unlock wording;
foreign progression flags do not imply equipment permission.

## English and translator resources

English ships now. The game selects its language through `game.translate_string`.
The generated reference is
`mod/gamedata/configs/text/eng/st_gamma_ap_notices.xml`; `tools/build.py` generates
the transfer and join templates from `notice_text.py` and every owned reward label
from the authoritative catalogue. Do not hand-edit the generated English file.

To add a translation, copy the string table into the game's appropriate language
directory, retaining stable string IDs. Translate complete sentences and reward
labels. Each transfer sentence must contain exactly one `{player}` and one
`{item}`; their order can change. Do not add PDA markup, controls or other placeholders. Missing,
malformed or unsafe translations fall back to English. Missing reward translations
use the companion's canonical label. Foreign-game reward labels remain upstream
data-package text, even if an ID matches a GAMMA item. Names are never translated.
Substitution is a single pass: placeholders inside labels remain literal data.

The join sentence uses exactly one `{player}` placeholder and no `{item}`. It
names this game's authenticated AP slot/alias, not its generated STALKER character.
It does not broadcast other players' joins into this game's PDA.

## Startup and reconnect notices

All automatic AP broadcasts (received rewards, sent rewards and joins) wait for
the native `on_loading_screen_dismissed` callback. An alive actor or an advancing
companion heartbeat is insufficient: actor updates can run while loading and at
the **Enter the Zone** prompt. The presentation gate additionally requires a
later device frame, zero precache frames, a present level, a living actor and an
unpaused device. It fails closed if those native signals cannot be inspected.
There is no timeout that releases notices behind the loading screen.

New-game initialization, save loading, actor destruction and the loading-screen
key prompt close the gate again. This transient flag is not saved. Deferred
transfer notices remain unacknowledged and unseen until actual display; normal
receipt application, loadout preparation and check synchronization continue.
Presence starts observing live heartbeat advances after the gate opens, so a
cached file still cannot announce a join. Already displayed transfer identities
retain their existing save/load deduplication.

Source basis: the installed development `callbacks_gameobject.script` forwards
the prompt and dismissal separately. The pinned
[Monolith loading implementation](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrGame/GamePersistent.cpp)
emits dismissal from `update_game_loaded` and from the no-keypress path; its
frame loop stops the loading renderer afterwards. The extra frame and precache
checks avoid displaying from inside the dismissal callback. The extracted
Anomaly `lua_help.script` documents `device().frame`, `precache_frame` and
`is_paused`. Saved-profile loose-file inspection is source evidence; native
timing and the engine's loaded winner still require Owen's verification.

The connected companion atomically publishes optional `presence.txt` version 1:
header `GAMMA_AP_PRESENCE|1`, session key, configuration digest (or `-` for an
unconfigured legacy pilot), a 16-hex connection epoch and monotonic sequence,
UTF-8-hex player label, then `end|1`. The entire snapshot is at most 2,048 bytes.
This presentation-only channel has no item/check acknowledgement fields.

The game waits to observe an advancing heartbeat before showing the join message.
A static file left by a stopped companion cannot announce a new connection.
The notice appears once per game load and per observed reconnect, including a
new companion epoch or a heartbeat resuming after more than five seconds. Clock
rollback resets this transient presentation cache. PDA ownership does not gate
the broadcast. Failed display retries on a later heartbeat.
Wrong-session/configuration, partial, malformed and
unsafe snapshots are refused. Old companions simply show no join message.

No save schema, published IDs, receipt handling or generation logic changes.
Translation fallback is English. The normal installation and private developer
panel are outside this source change. Deploy the companion and game module
together; an APWorld-only settings regeneration is not required for this feature.

No translated language pack is claimed. Font coverage, language selection and
native PDA rendering remain in-game acceptance for the user.

## Transport and save compatibility

Incoming notices use receipt identities and wait for the save's applied-item
count. Outgoing notices use source location, recipient and item, from real server
ItemSend confirmation and the durable recovery journal. Self-awards show only the
incoming notice. Notices never create inventory objects. No-PDA settings do not
delay broadcasts or reward application. Successful display identities are
saved separately; failed display cannot repeat item application.

The optional `notices.txt` sidecar now supports semantic version 2:

```text
GAMMA_AP_NOTICES|2
session|<session key>
notice|<identity>|<minimum receipt>|<kind>|<player UTF-8 hex>|<item UTF-8 hex>|<owned item ID or 0>
end|1
```

Kinds are `received_item`, `received_unlock`, `sent_item` and `sent_unlock`.
Version 2 can also carry legacy text records:
`notice|<identity>|<minimum receipt>|text|<UTF-8 hex>`.
The new add-on accepts original version 1 text snapshots unchanged. The encoder
retains version 1 for entirely legacy batches. Upgrade companion and add-on
together: an old add-on cannot display new semantic sidecars. Receipt/check
protocols, acknowledgement version 1, published IDs and save schemas are unchanged.
Previously saved notice identities remain valid and prevent redisplay.

Each snapshot binds to the session key, contains at most 16 notices and displays
at most one per normal poll. Malformed, oversized, wrong-session and unsafe text
is rejected. Labels are bounded and sanitized, then UTF-8 hex encoded across the
ASCII sidecar. The native API is `give_game_news` with the Archipelago header.

Foreign IDs retain Archipelago 0.6.8's signed 53-bit range exactly as decimal
identity strings, including in Lua acknowledgements. Negative zero, leading
zeros and out-of-range values are rejected. The server remains authoritative for
checks and item history; a notice acknowledgement is never an item receipt.

## Acceptance

Automated tests cover grammar, translation selection/fallback, resource parity,
opaque labels, foreign ID collisions, both sidecar versions, mixed batches,
malformed semantic records, saved identity replay and real server transfers.
Lua executable-line coverage is measured; Lua branch coverage is not measured.

Native acceptance is **not run** and reserved for the user: check all four English
sentences, self-awards, broadcasts without a PDA, reconnect and ordinary save/load;
confirm readable history/icons/fonts. A translation pack additionally needs its
own selected-language and missing-key fallback checks. Automated coverage and real
AP traffic do not establish engine rendering.

Startup-message acceptance additionally needs a live connected game load,
disconnect/reconnect, no-PDA broadcasts and a cached sidecar while the companion is
stopped. These native checks are **not run**. Automated tests exercise their
equivalent decisions with a mocked engine and actual AP connection/reconnection
traffic separately.

Loading-readiness acceptance additionally needs: leave **Enter the Zone** visible
while rewards arrive; confirm no AP popup is displayed; enter the world and
confirm pending notices appear once. Repeat after a save reload and a map
transition, and with the loading keypress option disabled. These native checks
remain **not run**. Previously displayed history is retained; this fix does not
erase or replay earlier popups.
