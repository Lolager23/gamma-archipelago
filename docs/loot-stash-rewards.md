# Step 14: optional loot stashes

Stack base: rank PR #17. `rewards_loot_stashes` enables 27 coordinate items:
Basic, Field and Advanced packages for supplies or eight ammunition families.
Their published IDs are 28051101–28051127. Existing physical item IDs and default
seed pools are unchanged. Expanded slots advertise their exact allowed item IDs;
old slots without that manifest retain their existing physical rewards.

Each receipt selects one of 17 named, unowned native Cordon containers from the
installed treasure manager's actual object roster. The seed/session, receipt and
item deterministically choose the box. Receipt state stores its identity and
fixed payload before revealing coordinates; reload never rerolls it. Different
packages can share a container. Native loot and native markers remain untouched.
Missing containers or payload sections keep the receipt pending with an error.

The Monolith DXML entry point adds AP-owned marker definitions to the installed
PDA map XML through its additive hook. Both loot and progression markers now use
an original rainbow backpack texture; their text hints distinguish their purpose.
Opening the actual box fills its saved creation plan during the use callback,
before GAMMA's next loot-screen refresh. The callback creates at most 64 objects;
an exceptionally large shared-box backlog reports that reopening will continue it.
The timed retry path still creates at most eight objects per poll.
Taking an identified AP-created item claims the marker;
remaining package actions still finish. Unrelated native loot cannot claim it.
Creation failures retry; exceptions or unsupported returned identities stop
automatic retry because creation may already have happened. Manual recovery is
required for that uncertain outcome. Ordinary older-save rollback can replay
physical loot, matching the documented consumable policy; crash-proof exactly
once creation is not claimed.

The initial finite roster is deliberately Cordon-only. Some native caches have
environmental hazards. White filler coordinates promise a known box and fixed
contents, not a safe approach, worldwide distribution or engine-verified geometry.
Ammunition quantities count standard native boxes, not an assumed round count.
Payloads exclude every eligible artefact-check section, preventing reward feedback.

The complete verifier passes 445 covered tests and two real-server cases. Owned
Python lines/branches and Lua executable lines measure 100%; Lua branch coverage
is not measured. Tests cover optional generation, exact item manifests, fixed
plans, save/load, shared boxes, marker ownership, missing APIs, bounded creation,
uncertain side effects and preserving checks while reward delivery fails. Native
treasure-manager, DXML and item-creation APIs were inspected in installed sources.
In-game marker rendering, cache access and loot interaction are **not run**,
reserved for the user's post-merge acceptance. No deployment or game launch ran.

## Missing-marker crash correction

A reported mutant-kill crash reached stash reward delivery and the engine's
`CMapLocation::LoadSpot` assertion for missing `gamma_ap_loot`. This is a native
fatal assertion; Lua `pcall` cannot turn it into a retryable error.

The inspected development `dxml_core.script` implements `query` as a descendant
search. A `map_spots` document root therefore does not match `query("map_spots")`.
The patch now uses `getRoot` and `getElementName`, inserts each missing AP-owned
node independently, then verifies exactly one of each of the four white/orange
marker and spot definitions. Standard, `_16`, `_21` and `_219` filenames are
supported. Native nodes and already-present owned definitions are preserved.

Hook registration alone no longer permits stash delivery. Both new receipts and
saved-stash polling wait for verified definitions before entering native marker
APIs or creating stash contents. Missing definitions leave the receipt/plan
pending with a bounded diagnostic; later successful initialization retries it.
This transient capability adds no save fields and changes no IDs or protocols.

Regressions model DXML's root/descendant distinction, partial and duplicate
definitions, failed insertion, and saved-plan recovery without duplicate spawning.
The fix's native marker rendering and kill-triggered reward acceptance are
**not run**. Its PR does not deploy code or change the current AP session, either
game installation, the local developer panel or third-party compatibility fixes.

## Empty loot-screen correction and rainbow markers

The previous use callback only set `opened=true`; creation waited for a later
500 ms actor poll. The active GAMMA inventory script (`LMode_Init` and `Update`)
refreshes a box on its next UI frame, so that refresh can happen before any AP
loot exists. Creation now runs in the same use event, matching the inspected
native treasure manager's timing. It does not prefill unopened boxes for NPCs to
scavenge, replace the native treasure manager or alter native loot/markers.
Identity, live actor and marker readiness are checked before
creation. Saved plans, completed action identities and uncertain-result stops
remain authoritative. Previously opened but unfinished stashes resume on use;
objects already recorded as created are never automatically replaced or duplicated.
If recorded loot was taken or lost, this fix cannot safely infer a replacement.
The tracker counts an actual saved claim, rather than merely opening the box.

`tools/build_stash_icon.py` draws the original 64px rainbow backpack and emits a
deterministic uncompressed RGBA DDS. Its additive texture descriptor is discovered
by pinned Monolith's `CMainMenu::ReadTextureInfo`; `CUITextureMaster` resolves its
owned texture ID. Both existing AP marker kinds remain separate and keep their
saved names. The packager accepts binary bytes only for this exact, regenerated
owned icon, leaving the rejection of foreign assets and linked files intact.

Regressions reproduce the old empty interaction without an intervening actor
update, recover legacy pending plans, verify bounded shared-box creation/reopening,
refuse invalid containers and capability failures, and preserve saved delivery
identities across reload. Other tests check DDS format, six colours, alpha, XML
resolution, byte-preserving packaging and rejection of foreign/corrupt textures.
Native rendering and stash interaction acceptance remain **not run**, for Owen.


## Physical stash access without a PDA

The native chimney container was confirmed as a pending AP ammunition-stash plan.
The save retained `opened=false`, `next_action=1` and no created object identities.
The earlier adapter silently skipped every stash use when no physical PDA was
available, even though coordinates had already been received. This artificial
condition could present a valid marked stash as empty.

Physical stash interaction now requires the saved coordinate plan and matching
container, but no PDA. Both ordinary packages and the protected psi-helmet claim
use the same rule. AP generation likewise removes the PDA permission from its
local Cordon psi-stash event; coordinate receipt and regional reachability remain
required. The PDA information/tracker and task equipment gates remain separate.

Existing unopened plans fill on the next valid use, before the loot UI refresh.
No seed reset, save edit, receipt replay, forced replacement or reroll is used.
Created identities, uncertain-result stops, live-actor checks and marker readiness
remain enforced. Regressions reproduce the chimney package with a locked/absent
PDA, protected delivery, save/reload and duplicate-use prevention. Native acceptance
is **not run**, reserved for Owen; private save evidence stays outside Git.
