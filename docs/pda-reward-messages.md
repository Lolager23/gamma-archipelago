# PDA reward messages

The companion preserves player and item labels and publishes optional notices to
the game's PDA news API. English examples:

- `Friend gave you "Basic Toolkit".`
- `Friend unlocked your "Zone Access".`
- `You sent "100 Rupees" to James.`
- `You unlocked "Zone Access" for James.`

Quoted item labels work with plurals, currency, acronyms and foreign-game names
without guessing an English article. Outgoing messages avoid possessive-name
rules. Only explicitly known GAMMA unlock and skill effects use unlock wording;
foreign progression flags do not imply equipment permission.

## English and translator resources

English ships now. The game selects its language through `game.translate_string`.
The generated reference is
`mod/gamedata/configs/text/eng/st_gamma_ap_notices.xml`; `tools/build.py` generates
four whole-sentence templates from `notice_text.py` and every owned reward label
from the authoritative catalogue. Do not hand-edit the generated English file.

To add a translation, copy the string table into the game's appropriate language
directory, retaining stable string IDs. Translate complete sentences and reward
labels. Each sentence must contain exactly one `{player}` and one `{item}`; their
order can change. Do not add PDA markup, controls or other placeholders. Missing,
malformed or unsafe translations fall back to English. Missing reward translations
use the companion's canonical label. Foreign-game reward labels remain upstream
data-package text, even if an ID matches a GAMMA item. Names are never translated.
Substitution is a single pass: placeholders inside labels remain literal data.

No translated language pack is claimed. Font coverage, language selection and
native PDA rendering remain in-game acceptance for the user.

## Transport and save compatibility

Incoming notices use receipt identities and wait for the save's applied-item
count. Outgoing notices use source location, recipient and item, from real server
ItemSend confirmation and the durable recovery journal. Self-awards show only the
incoming notice. Notices never create inventory objects. No-PDA settings defer
display without blocking reward application. Successful display identities are
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
sentences, self-awards, absent PDA/deferred news, reconnect and ordinary save/load;
confirm readable history/icons/fonts. A translation pack additionally needs its
own selected-language and missing-key fallback checks. Automated coverage and real
AP traffic do not establish engine rendering.
