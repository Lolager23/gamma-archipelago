# PDA reward messages

The companion preserves player and item labels and publishes optional notices to
the game's news API. Archipelago broadcasts appear without owning a PDA,
including when the starting PDA is omitted or AP-locked. English examples:

- `Friend gave you "Basic Toolkit".`
- `Friend unlocked your "Zone Access".`
- `You sent "100 Rupees" to James.`
- `You unlocked "Zone Access" for James.`
- `GammaPilot loaded GAMMA and entered the Zone.`

## Why a reward was earned

Transfer announcements finish with the source check, for example:

- `You unlocked "Equipment Unlock: PDA" for Owen by entering Rookie Village.`
- `Friend unlocked your "Zone Key: Garbage" by entering Rostok.`
- `Friend gave you "Bandage" by killing 15 hostiles.`
- `You sent "Basic Toolkit" to James for reaching Legend rank.`

The companion resolves the source slot's game and `NetworkItem.location`, not the
recipient's game or the item ID. GAMMA causes come from the authoritative check
catalogue, including maps, settlements, first mutant/faction kills, distinct-type
quotas, artefacts, task types, side-task/kill totals, gear tiers/upgrades, story,
rank, purchases and goodwill. Hostile totals include stalkers; distinct mutant
types are explicitly described as distinct types rather than repeated kills.

Other games use their source slot's data-package check name: `by completing
"Defeat the Dragon"`. Numeric ID collisions cannot turn a foreign check into a
GAMMA action. Server/starting/cheat deliveries use their actual upstream source
label (`from "Server"` or `from "Cheat Console"`) rather than inventing a check.
Unknown source metadata delays only the notice until its data package arrives;
item history/application continues normally.

Incoming announcements wait until their ordered reward has actually applied.
If a native reward fails, later incoming rewards and their announcements remain
pending; independent check reporting continues to the server. For example, a
skill compatibility error can hold a later artefact reward even though its check
is confirmed. Fixing the native adapter lets the same saved session retry the
pending receipt. Notices already acknowledged are not repeated.

The Haruka adapter supports the original 15-level cap and the active GAMMA
"Skill System Balance" 30-level cap. Both use the inspected native level/stat
increment formula. Other cap values remain unsupported and leave the reward
pending. Failed recalculation retains its saved target for retry without adding
the level again; a capped skill consumes the receipt without exceeding its cap.

This presentation update does not change checks, rewards, IDs, settings digests
or save schemas. Notice identities and acknowledgements remain unchanged, so
already displayed announcements are not replayed merely to add their cause.

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

Causal transfer templates use the additional `{cause}` placeholder exactly once:
`gamma_ap_notice_<kind>_cause`. Cause fragments use exactly one `{value}` in
`gamma_ap_cause_<cause kind>`. Generated `gamma_ap_cause_value_<kind>_<UTF-8 hex>`
entries translate catalogue-backed values such as map, rank and artefact labels.
Dynamic milestone numbers retain their canonical decimal values when a value
entry is absent. Foreign check/source names stay upstream data, even if a value
matches an owned label. Each template layer substitutes once; braces inside
names/labels are never interpreted as another placeholder. Invalid or missing
translations fall back independently to the English sentence, cause or value.

The old join string remains generated for older matching bundles. Current world-entry
news is ordinary AP room chat and identifies the authenticated slot. Real upstream
Join/Part messages retain their network-connection meaning.

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
World-entry requests wait for a fresh authenticated companion status after the gate
opens, so a cached file cannot announce entry. Already displayed transfer identities
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

The companion still publishes `presence.txt` version 1 for older matching bundles.
The current add-on uses `connection_status.txt` and its challenge-bound game request
queue instead; it does not translate heartbeat advances into local join messages.
A first ready-world entry sends one room announcement. Level switching, save/load
and heartbeat reconnects do not generate another entry request in that game process.
See the world-entry correction below for queue ownership and delivery limits.

No save schema, published IDs, receipt handling or generation logic changes.
Deploy the companion and game module together; an APWorld-only settings
regeneration is not required. The normal installation and private developer
panel are outside this source change.

No translated language pack is claimed. Font coverage, language selection and
native PDA rendering remain in-game acceptance for the user.

## Transport and save compatibility

Incoming notices use receipt identities and wait for the save's applied-item
count. Outgoing notices use source location, recipient and item, from real server
ItemSend confirmation and the durable recovery journal. Self-awards show only the
incoming notice. Notices never create inventory objects. No-PDA settings do not
delay broadcasts or reward application. Successful display identities are
saved separately; failed display cannot repeat item application.

The optional `notices.txt` sidecar supports semantic version 2:

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

Version 3 adds structured check causes:

```text
GAMMA_AP_NOTICES|3
session|<session key>
notice|<identity>|<minimum receipt>|<kind>|<player UTF-8 hex>|<item UTF-8 hex>|<owned item ID or 0>|<cause kind>|<cause value UTF-8 hex>
end|1
```

Mixed version-3 batches represent semantic records without a cause with
`|none|` (empty cause value). They also accept the version-2 legacy `text` form.
The encoder retains version 1 for text-only batches and version 2 for semantic
batches without causes. The add-on reads all three versions and rejects malformed
or unknown causes. Upgrade companion/APWorld adapter and add-on together: old
add-ons cannot display version 3. The AP server and existing seed can be retained;
only the companion needs a restart after installing the matching bundle. Receipt,
check, save and acknowledgement formats are unchanged.

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

Cause acceptance additionally needs sent/received/self awards from different
check categories, a foreign-game source, selected-language fallback, loading
readiness and save/load without replay. These checks remain **not run**.

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


## Direct inventory delivery from a stash

A protected stash, currently the calibrated psi helmet, delivers its contents
straight into the actor's inventory. On successful completion it queues a local
PDA news entry, for example:

`Archipelago stash: "Calibrated Psi Helmet" was delivered directly to your inventory.`

The next ready-world stash poll displays at most one queued entry. Loading,
precaching and paused frames defer it. The item uses its native translated
inventory name when available, then the existing owned reward translation or
catalogue label. The complete sentence is translation-ready in the hand-authored
`mod/gamedata/configs/text/eng/st_gamma_ap_stashes.xml` resource, under stable ID
`gamma_ap_stash_inventory_delivery`, with exactly one `{item}` placeholder.
Missing or unsafe translations fall back to the complete English sentence.

The central saved stash record owns an optional boolean `inventory_notice_pending`.
It is set only after a protected delivery finishes and is cleared after the news
API succeeds. A failed notice never reopens the creation plan or blocks later
reward receipts. Marker cleanup failure does not hide an already delivered reward.
Saving before display retains the pending notice; saving after display prevents
reopening/reloading from repeating it. An older claimed stash without the flag
never replays a historical delivery. Ordinary box loot does not emit this notice.
Normal older-save rollback or a crash before saving can replay a message; there
is no new exactly-once engine transaction guarantee. No network notice identity,
acknowledgement, item/check ID, configuration digest or save schema version changes.


## Room-wide news (26 November 2026)

The matching companion and add-on also project live room messages, including
foreign self-awards (Dave finding an item for Dave). The finder and recipient
names, recipient game's item namespace and finder game's source-check namespace
remain distinct. Missing metadata defers presentation only. Duplicate live
ItemSend packets are suppressed by their finder/location/recipient/item identity.
Local transfers retain their saved notices and incoming receipt boundary; the
room feed does not duplicate them or claim delivery in someone else's inventory.

`room_feed.txt` is an optional bounded presentation snapshot, tied to the exact
session/configuration, with a process epoch, advancing heartbeat and the last 64
messages. The game waits for world readiness and an observed heartbeat advance,
then displays at most one message per poll. Its cursor survives level/save loads
within the process. A stopped companion cannot initiate announcements from a
cached file. Room news is transient, not a durable chat archive or saved item
acknowledgement; sufficiently long absences can exceed the 64-message window.
English room transfer prose uses upstream labels and the existing check-cause
projection. Local reward localization and receipt/check protocols are unchanged.
Native acceptance remains not run and belongs to Owen. No live session changed.


## World entry and diagnostics correction (26 November 2026)

The old "joined the Archipelago" popup was a local heartbeat notification,
reset by game load and reconnect. It did not announce a real network join to the
room. The new bundle removes that local announcement. Real upstream Join/Part
news retains its actual connection meaning in the room feed.

After the first ready-world load in the game process, a challenge-bound game
request asks the connected companion to send "<slot> loaded GAMMA and entered the
Zone." through upstream Say. It is ordinary room chat, visible to other AP
clients. Loading gates delay the request; level switches and save reloads do not
reset its transient queue/acknowledgement. The companion deduplicates requests
across reconnects in that process. A restarted game creates a fresh request epoch.
Old request files cannot be replayed by a new companion challenge. Requests use
a separate bounded 32-entry data queue and never alter checks or item receipts.
Submission acknowledgement means the websocket write completed, not that every
other client displayed the message; chat has no crash-proof delivery guarantee.

The MCM "Show Archipelago connection status" button prints local news and a
console line with the authenticated connection status and count of local checks
absent from the exact server-confirmed snapshot. Stale heartbeat/status is explicit;
missing or malformed confirmations report an unknown backlog. Server labels
exclude URL credentials, query strings and paths. Offline status continues to be
published while the companion retains a bound session. No normal game, active
session, developer panel, IDs or saved receipt/check state is changed.

This requires matching companion and game packages. Native loading, MCM rendering
and level-switch acceptance remain not run, reserved for Owen.
