# Shared faction goodwill and existing-run conversion

New generation defaults `shared_faction_goodwill` on. With faction rewards enabled,
the pool guarantees twelve `Faction Goodwill: All Factions` rewards (new stable ID
28051309), each granting +250 personal standing to Free Stalkers, Clear Sky, Duty,
Freedom, Ecologists, Mercenaries, Military and Bandits. The AP-earned floor caps at
3,000 per faction; naturally higher standing is preserved. Global alliances,
actor community and individual NPC grudges remain native.

Each shared copy credits each faction separately. A shared copy and a named Duty
copy contribute two Duty copies; separate Duty/Freedom copies are never summed
into one faction. The same projection supplies placement rules, standing/rank
proxies and the PDA. Five shared copies cover the supported hostile-base quotas.
The twelve-copy budget replaces the former twelve-Loner and separate five-copy
hostile-faction guarantees. Starting shared gifts reduce the generated quota;
starting-from-pool consumes it normally. Too few reliable checks fail generation.
Extra-goodwill quantities add shared copies in this mode. Named legacy rewards
retain their IDs and remain supported for explicit starting items and old seeds.

Missing mode fields decode as zero and do not alter older digests/wire snapshots.
New shared rewards are absent from those manifests. Disabling the setting restores
faction-specific generation. New seeds require matching APWorld/client/mod bundles.

## Explicit conversion of an existing run

The optional game-owned migration record upgrades only the old Loner reward,
28051301, for one explicitly selected existing session. No seed is regenerated,
server archive rewritten, location moved, receipt ID replaced or check released.
Existing faction-specific rewards elsewhere in that seed remain and still stack
within the cap. Raw AP server item names remain the original Loner label;
semantic incoming PDA notices use the shared label after conversion.

After stable full appdata/profile/configuration and server-save backups, an operator
places this fixed data-only request in the selected game's enrolled bridge folder:

```text
GAMMA_AP_GOODWILL_MIGRATION|1
session|<existing 64-character lowercase session key>
configuration|<existing 64-character lowercase configuration digest>
convert_loner|1
end|1
```

The filename is `goodwill_migration.txt`, with a trailing LF and maximum 512 bytes.
Wrong sessions/configurations, malformed requests and an already-shared new seed
are refused. Without a request or saved conversion, legacy behavior is unchanged.

On the first ready-world update the adapter counts already-applied Loner receipts,
reads all seven other factions and records absolute backfill targets before any
standing mutation. It then applies the targets and marks the saved migration
complete. A setter failure resumes those same targets; later income is preserved.
A pre-existing pending scalar Loner target is reused when that receipt becomes
shared, preventing an extra Loner grant. Future Loner receipts grant all eight
factions through the normal ordered receipt path. No consumable items are spawned.

The optional `goodwill_migration` save field binds its version, session, digest,
basis receipt count, Loner count, seven targets, completion and pending PDA notice.
Existing numeric goodwill targets remain valid; new shared receipts use detached
per-faction targets. Validation runs before copying/loading the state. A completed
conversion remains active if its request file is removed. Restoring an older save
restores its matching native standing and derives its conversion from that save's
receipt history when the request remains present. The permanent earned floor
continues to reconcile while the bridge is offline.

Display, native mutations and saving are separate operations, not a crash-proof
exactly-once transaction. Keep the verified pre-update backup. Downgrade a migrated
run only by restoring its matching pre-update bundle and save; do not edit receipt
history or remove only the migration flag. Native acceptance remains with Owen
and Mini; agents must not launch/load GAMMA.
