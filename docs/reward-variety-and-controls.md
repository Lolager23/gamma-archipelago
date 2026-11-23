# Reward variety and generator controls

Requested 23 November 2026. These increments stack after the skill-delivery
compatibility fix. Native acceptance belongs to Owen; current sessions and the
normal installation remain untouched unless deployment is separately authorized.

| Increment | Intended behaviour | Status |
|---|---|---|
| Varied stash contents | Tier/calibre-aware supplies, ammo variants and quantities; saved once | Implemented; affected verification pending |
| Practical Cordon faction budget | Two dependable faction opportunities; no opening Military assumption | Implemented; affected verification pending |
| Useful randomized rewards | Varied supplies/ammo rather than alternating Bandage/Medkit filler | Implemented; affected verification pending |
| Generator controls | Clear reward controls with sliders and exact manual counts, enabled-state and pool feedback | Planned |

## White stash rolls

`randomized_stash_loot` defaults on for newly generated configurations. Omitted
older fields mean zero and retain the previous digest/wire format. Existing seed
archives are not refilled. Disabled randomization retains fixed legacy contents.
Orange quest/tool progression contents are never randomized.

The authoritative catalogue owns version-1 profiles and item/calibre alternatives.
Basic, Field and Advanced stashes have respectively 3–6, 5–8 and 7–11 supply items,
including at least one curated item at that quality tier. Named ammunition stashes
add respectively 1–3, 2–5 or 3–7 boxes of their advertised calibre. Field/Advanced
tiers can include the supported alternate ammunition variant. Supplies-only stashes
remain consumable/maintenance packages. Ammo counts refer to boxes; rounds per box
remain native GAMMA behaviour.

A local deterministic generator uses the complete session key, item and receipt
index. It does not consume global game randomness. The complete ordered action
plan is stored before coordinates are acknowledged, and validated against its
versioned roll on load. Reopening, retries and save/load preserve quantities,
sections and creation markers. The engine decides final inventory-cell layout;
AP varies the loot mix and frozen creation order.

Legacy records with no roll version retain exactly their original contents,
including already opened or partially created packages. New records include
`loot_version = 1`; older adapters reject those unsupported plans. Keep the
pre-upgrade backup for downgrading. Spawning and saving are not atomic: uncertain
creation still blocks automatic replay, rather than promising crash-proof delivery.

## Dependable faction opportunities

Cordon contributes two supported faction types, Free Stalkers and Bandits, to
generation and the PDA regional projection. Military's curated source is now
Agroprom, supported by the enabled NPC Spawns configuration's
`agr_smart_terrain_1_6` / `agr_smart_terrain_1_6_near_1` novice/advanced army squads
before Brain Scorcher shutdown. Cordon's checkpoint is not treated as a practical
opening requirement. Opening Great Swamps adds Clear Sky and Renegade opportunities.
Configured source exclusions continue to reduce quota capacity.

This is a solver assumption, not an engine kill restriction. An actual qualifying
Military kill in Cordon still records its discovery and can complete the next
generic quota. Named Military checks also use the Agroprom source requirement.
Fresh worlds fill with the corrected requirements; existing archived placements
and completed observations are never rewritten. Native spawn/pacing acceptance
remains Owen's. The five-type starting mutant budget is unchanged by this increment.

Pacing repair also accepts equal-count swaps that move the earliest collision
later, before attempting another separation. It still requires every check and
goal reachable, early recipes preserved and zero final tier collisions. This
avoids the slow repair plateau exposed by the two-faction opening; it adds no gates.

## Spare-slot reward variety

`varied_filler` defaults on for new generations and omitted legacy fields retain
zero. After mandatory progression, convenience minima and requested repeatable
copies are reserved, spare slots draw weighted non-progression rewards from
enabled categories. Seventeen new supply rewards (IDs 28051920–28051936) provide
better medicines, repair supplies, named ammunition boxes and expedition supplies.
Basic/Field white stashes can also fill spare slots. Advanced stashes remain useful
rewards with their requested copies; protected filler-only checks never gain useful
or progression items merely because a supply has a higher native value.

Standalone Bandage/Medkit filler is absent when any enabled alternative exists.
If all alternatives are disabled, basic supplies remain the fallback. Turning the
option off retains the original filler policy and removes the new IDs from the
slot manifest. Existing seed archives are unchanged. In explicit quantity mode,
named package counts remain exact: extra single-supply drops have distinct IDs
and do not consume or inflate guaranteed package counts. Ammunition names denote
the actual fixed section; the generic package-calibre selector affects only its
original configurable package. Native box sizes remain unchanged.

Drops reuse the central ordered delivery plans, without a second inventory or
receipt owner. Save/load preserves successful delivery; uncertain creation still
blocks replay. Native availability and balance need Owen's acceptance. Coordinated
world/client/game updates are required to use the new item IDs in a fresh seed.

## Follow-up boundaries

Faction modelling changes alter generation/PDA assumptions, never forbid actual
bonus kills. Required permissions are budgeted before discretionary rewards.
Progression minima must remain automatic; sliders cannot remove required copies
or place an unlock behind its own requirement. Manual values can exceed suggested
slider ranges within finite check/receipt limits, with actionable capacity errors.
Displayed estimates and native availability remain distinct from verified playtime.
