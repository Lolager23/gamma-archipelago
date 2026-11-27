For corrected allied sharing and the current-run repair, see [shared goodwill](shared-goodwill.md) and [manual repair](goodwill-repair.md).

# Step 16: faction goodwill rewards

New generations now use [shared goodwill](shared-goodwill.md): twelve rewards each
credit all eight supported factions. That document also defines the explicit,
session-bound migration for an existing run. The faction-specific behavior below
is retained for legacy seeds without that migration.

Current extension: [settlement reputation access](settlement-reputation.md)
guarantees five progression copies each for Military, Bandits and Mercenaries
when their hostile settlement gates are enabled. Other faction bonuses retain
the useful pool. Legacy seeds retain the native bonus and retry contract below.
For the three gated communities only, the new setting also preserves an AP-earned
minimum personal standing; other bonuses and legacy seeds remain mutable. The
permanent floor and its recovery contract are described in the linked extension.
The original Step 16 implementation/evidence is recorded below.

Stack base: #19. Eight optional useful rewards add 250 personal goodwill for
Loners, Clear Sky, Duty, Freedom, Ecologists, Mercenaries, Military or Bandits.
The cap is 3,000; an existing higher value is preserved. Negative goodwill is
improved by the same bounded bonus, not reset to friendly. Faction alliances,
actor faction, NPC forced relations and global character reputation are untouched.

The installed Economy trader configurations consult personal faction goodwill at
500/1,000/1,500/2,000 for supply tiers. This adapter updates that exact registry
through `community_goodwill` / `set_community_goodwill`. Native faction hostility,
other trader requirements and restock timing still apply; no stock refresh is
forced and receipt does not promise immediate trade with an enemy trader.

The save stores each receipt's absolute target before mutation. Retry verifies
that target instead of adding another bonus after an exception with side effects.
Receipt acknowledgement requires the getter to confirm the target. Higher natural
goodwill attained during retry is preserved. Ordinary saves restore both native
registry and AP state; older-save rollback replays the corresponding bonus.

Full verifier: 453 covered tests plus two real-server cases, all coverage gates
passed. Tests cover cap, higher existing goodwill, malformed/API failures,
setter failure after mutation, save/load and unconfirmed updates. Engine trader
refresh/eligibility acceptance is not run and belongs to Owen after merge. No
launch, deployment or changes to the protected installation were performed.
