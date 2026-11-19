# Step 14: optional white loot stashes

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

The Monolith DXML entry point adds AP-owned white and orange marker definitions
to the installed PDA map XML through its additive hook. This step uses only the
white marker. Opening the actual box enables a saved, bounded creation plan
(eight objects per poll). Taking an identified AP-created item claims the marker;
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
