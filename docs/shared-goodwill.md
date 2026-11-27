# Shared faction goodwill and existing-run conversion

New generation defaults `shared_faction_goodwill` to 2 (allied factions). The pool
includes twelve `Faction Goodwill: Allied Factions` rewards, stable ID 28051310.
Each grants +250 personal goodwill to Free Stalkers, Clear Sky, Duty, Freedom and
Ecologists. Mercenaries, Military and Bandits retain their separate named rewards
and hostile-base placement requirements. For the normal Living Legend preset,
that means twelve allied copies plus five copies for each of those three factions.
Starting gifts reduce the respective quotas; rewards cannot satisfy their own
base access. Extra goodwill quantities use the selected shared reward.

The permanent AP-earned floor caps at 3,000 per faction. Naturally higher standing
is preserved by ordinary reward delivery. Global alliances, actor community and
individual NPC grudges remain native. A shared allied copy and a named Duty copy
count as two Duty copies; the shared allied copy never counts for Military,
Bandits or Mercenaries. Solver rules, PDA projections and native floors agree.

## Published compatibility

Mode 0 remains faction-specific. Missing fields still decode as 0 with unchanged
configuration digests. Published mode 1 and ID 28051309 (`All Factions`) retain
their all-eight meaning for existing seeds. The corrected allied semantics use
mode 2 and a new ID instead of silently changing a published reward. Legacy toggle
names remain aliases for modes 0/1. New seeds need matching world/client/mod files.
Existing archives, check history, slot IDs and ordered items are not rewritten.

## Converting an existing legacy run

The data-only request is still `appdata/archipelago/goodwill_migration.txt`, bounded
to 512 bytes, with a trailing LF and the exact existing session/configuration keys.
Old version-1 requests and saved plans retain their original all-eight semantics.
New conversions should use version 2:

```text
GAMMA_AP_GOODWILL_MIGRATION|2
session|<existing lowercase 64-character session key>
configuration|<existing lowercase 64-character configuration digest>
convert_loner|1
scope|allied
end|1
```

A new plan credits only the four other allied factions for already-applied Loner
receipts and makes later Loner receipts affect those five allied factions. Saved
absolute targets survive partial failures and save/load. The existing Loner target
is reused for a pending scalar receipt. The optional `scope=allied` save field
keeps old nil-scope records readable. A new request does **not** undo a completed
old migration: that needs the explicit repair below.

## Repairing an already-applied all-eight conversion

See [manual repair](goodwill-repair.md). The old migration did not record original
standings or the exact per-faction delta after caps/floors, so the mod cannot claim
an exact reconstruction of natural goodwill. The repair is deliberate and saved,
not an automatic subtraction on load. It preserves checks, items, receipts and
quests, and only corrects the three supported hostile factions.

Display, native mutations and game saving are separate operations. This is not a
crash-proof exactly-once transaction. Keep matching pre-update appdata/profile/
configuration backups. Downgrade only with their matching mod/save backups. Native
acceptance remains with Owen and Mini; agents must not launch/load GAMMA.
