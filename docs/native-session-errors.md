# Native session error review — 25 November 2026

The recent development game log spans repeated load/start cycles (50 adapter
initializations). These counts describe that whole log, rather than one load.
The companion/server logs cover the current Owen/Mini session. No fatal engine
crash record was found; normal logger shutdown is present. Live acceptance is
not run: Owen owns in-game verification.

## Confirmed transition binding error

The log contains 31,545 instances of `CSpaceRestrictor [level_changer]: cannot
access class member inside`, with stacks in `gamma_ap_zone_keys.guard_changer`.
Level changers expose position but reject this inherited restrictor method.
The warning now uses a bounded ten-metre distance. Access still uses the native
disable flag and packet/script guards. Recovery also removes the unsupported
call: full ALife shape bounds and inverse exits remain in use, with an additional
thirty-metre clearance around online changer positions. Tests make `inside`
raise, and cover remote warning suppression, silent triggers, extra transitions,
geometry clearance and refused unsafe recovery.

## Findings needing further diagnosis

- Equipment stowing failed 49 times; another 37 messages report equipment
  enforcement failure. The log identifies the AP path but not the item/slot or
  native transfer outcome, so it does not establish a specific root cause.
- The companion recorded 51 Windows access-denied replacements across presence,
  notices and scouting files, plus 14 incomplete snapshot/acknowledgement reads.
  This is consistent with transient file contention or a read during a native
  write. Later cross-player transfers continued; a permanent delivery failure
  or lost checks is not established by these logs. Existing ordered history,
  acknowledgement validation and retries must be preserved.
- Fresh-loadout and supported-story-faction warnings appear during repeated
  initialization. Later successful activity means these are not evidence that
  every loaded save was rejected. Investigate initialization ordering separately.

Other Lua stacks originate in silencer-condition, autoloot and safespawn scripts;
this review does not attribute those failures to Archipelago. Server warnings
about the optional C++ speedup and initial host settings are informational.

Raw logs, save identities and installation inventories remain private outside
Git. Neither the normal game nor seed placements are changed by this review.

Affected verification passed 1,250 Lua regressions. Both changed transition
modules reached 100% executable-line coverage; Lua branch coverage is not
measured. Static checks and deterministic packaging passed. Current-head
Windows/Linux CI is tracked on the PR. IDs, configuration digests, receipt
history, saved checks and seed placements are unchanged.
