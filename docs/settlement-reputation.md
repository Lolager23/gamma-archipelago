# Settlement reputation access

New generations default `settlement_reputation_logic` on. Free Stalker hostility
now affects settlement access rules and progression budgeting. No faction alliance,
actor community, NPC forced relation or personal NPC grudge is changed by this
feature. Native testing is **not run**, reserved for Owen.

## Reviewed settlements

| Settlement | Default community | Progression policy |
|---|---|---|
| Southern Checkpoint | Military | Five Military goodwill rewards / neutral native standing |
| Agroprom Research Institute | Military | Shares the same five Military rewards |
| Bandit Base, Dark Valley | Bandits | Five Bandit goodwill rewards / neutral native standing |
| Mercenary Base, Dead City | Mercenaries | Five Mercenary goodwill rewards / neutral native standing |
| Sin Mine Barracks | Sin | Filler-only: no supported goodwill reward route |
| Monolith Cultural Center | Monolith | Filler-only: no supported goodwill reward route |

The other twelve hubs remain ungated: Rookie Village, Old Farmstead, Clear Sky
Base, Train Depot, Agroprom Factory, Rostok, Freedom Base, Sakharov Bunker,
Skadovsk, Yanov Station, Hermann Bunker and Laundromat. Names alone are not a
community test: Hermann's `jup_b47_merc_guard_squad` uses Ecologist members;
Sakharov's military-labelled shop profiles use the neutral trader community.

## Threshold and pool

The inspected Free Stalker start resets personal community goodwill to zero.
The hostile community relation is -2,000 and the engine's neutral threshold is
-999, inclusive. Thus at least +1,001 personal goodwill is needed under ordinary
starting relations. Four +250 rewards give +1,000 and remain hostile; five give
+1,250 and cross the threshold. Two Military bases do not require ten rewards.

When faction rewards and these checks are enabled, generation reserves five
copies per supported hostile community before optional rewards. Those copies
are progression, including when constructed for common starting inventory.
Their item IDs and names are unchanged. The other five faction bonuses stay
optional useful rewards. The three guaranteed types do not also enter the random
bonus pool: duplicate optional copies could obstruct a small finite pool.

If faction rewards are disabled, all six hostile settlement checks are filler-only.
Sin and Monolith remain filler-only even with `optional_check_policy=allow_progression`.
This is an unsupported-route protection, not a promise that those factions can
never become neutral through another mod or story circumstance. There is no new
Sin/Monolith reward and no automatic pacification.

Expanded worlds use normal AP fill. A cramped settlement-only pool can exhaust
its safe checks across three incomplete five-item quotas. For that case only,
an upstream early-item request favours the quota opening the most checks
(Military's two bases). It requests earned items, not a starting gift or a fixed
key location; normal/local early requests remain authoritative. Inadequate opening
capacity fails generation with an explanation. Required and bonus copies are
budgeted separately; no required reward is silently dropped.

Regional source evaluation shares repeated region lookups only within one query.
The cache is discarded before the next AP state evaluation; no stale access result
or additional persistent state is introduced as the progression graph grows.

## Native checks and PDA

The AP solver models five received rewards as a conservative earning route. The
native entry callback instead checks current personal goodwill plus current
community relation against the neutral threshold. Natural goodwill can therefore
permit an earlier check. Entering at hostile standing leaves the check pending;
the normal repeated smart callback can complete it after standing improves.

The PDA accepts a read-only native standing projection and explains the current
goodwill deficit. Offline/model-only projections use applied AP receipt counts.
Missing or malformed native APIs and invalid actor identities fail closed, with
an actionable reason; invalid community names never reach native relation bindings.
Completed checks remain monotonic after hostility changes or save/load.

These ordinary community thresholds do not guarantee that a particular NPC stops
shooting. Scripted quest hostility, personal grudges, disguises and dynamic faction
wars can change individual eligibility; native acceptance remains required.

Owen selected a permanent AP-earned reputation floor. In these reputation-gated
seeds, each applied Military/Bandit/Mercenary reward contributes +250 to a minimum
personal standing, capped at 3,000. Higher natural goodwill is preserved. A new
receipt targets at least its earned floor, so earlier combat debt cannot prevent
the fifth reward from achieving ordinary neutrality. The adapter restores later
personal losses during its bounded update and before smart entry, including while
the bridge is offline. Other faction rewards retain their original mutable bonus.

The floor derives from the same validated applied receipt history; no separate
saved reputation counter exists. Setter failures retry the same target without
replaying receipts or compounding bonuses. Old-save rollback derives the older
floor until the server history is replayed. No global alliance or NPC forced
relation is rewritten, and no guarantee is made about unsupported faction-war
configurations exceeding the native goodwill cap. Completed checks are never lost.

## Compatibility and sources

Legacy snapshots omitting the new setting keep value zero, their original digest
and entry behaviour. Disabled settings are omitted from the old wire format;
enabled seeds require a coordinated APWorld/client/mod upgrade. Existing archives
and saves are never refilled or retrospectively un-checked. Selecting legacy
settlement access explicitly restores the earlier unrestricted placement policy.

Primary baseline evidence: active GAMMA Economy `creatures/game_relations.ltx`,
ZCP's `ui_mm_faction_select.script`, the effective `misc/simulation.ltx` and squad
descriptors, and effective `character_desc_yantar.xml`. Source inventories and
hashes stay private outside Git; no game assets are included. The pinned engine
[attitude calculation and neutral comparison](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrGame/relation_registry_inline.h)
confirm the sum and inclusive boundary. The
[goodwill registry](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrGame/relation_registry.cpp)
remains the native state owner.

Owen should test hostile entry without rewards, four versus five rewards, natural
neutrality, both Military bases sharing a quota, negative goodwill, save/reload,
completed-check retention, current PDA reasons and any forced-hostile NPCs in a
fresh coordinated Dev seed. No game launch or deployment is part of this PR.
