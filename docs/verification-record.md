# Verification record

## Live pilot observation: 18 November 2026, 23:34 UTC

The user reported that the triggers and rewards work. Independently inspected
the current local server log, its persisted `.apsave`, the game log and both
bridge snapshots. The deployed source is `a7995ef` on the MCM branch; these
observations do not imply that this documentation branch implements that PR.

| Check | Server confirmation | Game application evidence |
|---|---|---|
| Rostok: First Arrival, ID 28052003 | One recorded Bandage award; present in persisted server checks | Game log records `Received bandage`; acknowledged receipt history includes item 28051003 |
| Garbage: First Arrival, ID 28052002 | One recorded Basic Toolkit award; present in persisted server checks | Game log records `Received itm_basickit`; acknowledged receipt history includes item 28051001 |
| Cordon: First Arrival, ID 28052001 | Not present in the inspected server check set | Not independently verified in this session |

The persisted AP server history contains two items. The outgoing game snapshot
reports two applied receipts, Garbage/Rostok checks and `goal|0`. Incoming history
contains Bandage followed by Basic Toolkit. This proves two actual game-to-server
checks and two acknowledged server-to-game applications. It does not establish
the third check/reward, overall goal, another player's delivery or controlled
game save/reload recovery. The server save is beside the generated seed archive.

Private evidence was copied outside Git under `D:/GAMMAAPTools/diagnostics`.
The local session setup had backed up and SHA-256 verified 737 development
appdata/profile/overwrite/configuration files before launch. No personal saves,
runtime inventories or session archives are committed.

The user also confirmed the MCM toolkit button works. That manual action is
independent of AP receipt state and is not counted as a received AP reward.

## Current environment and compatibility

The official GAMMA installation completed successfully, as confirmed by the user.
The isolated GAMMA 0.9.5 menu was observed. The engine identifies as Modded Exes
MT-TEST2026.05.15, core 9959; Anomaly baseline is 1.5.3. Launch through
`D:/GAMMAAP/ModOrganizer.exe` with `Archipelago DEV` selected so the virtual mod
files are applied. The desktop AP DEV shortcut now opens that folder.

Game/appdata isolation is provided by `D:/AnomalyAP`, separate from the original
multiplayer installation. MO2's game plugin reports that profile-local saves are
unsupported; do not rely on that checkbox for isolation. The custom DX11 dev
entry uses `user_ap_dev.ltx`; ordinary dev entries use `user.ltx`. Their PDA key
bindings currently differ. No settings or saves are shared with the original.

The latest inspected game log contains four distinct third-party script failures:

| Script | Observed reason | Owning active component |
|---|---|---|
| `a_faction_prices` | Missing `faction_stocks` | GAMMA UI |
| `mags_patches` | Missing `magazine_binder` | UDP-9 compatibility script |
| `zz_ui_inventory_better_stats_bars` | Missing `better_stats_bars_mcm` | GAMMA Keybinds fixes |
| `zzz_mspizza_godis_zoomcalc` | Invalid Lua `/*` comment syntax near line 113 | 3DSS for GAMMA |

These four also appear in the pre-session log. They have not been repaired by
this planning increment. Extra Level Transitions is enabled and its scripts have
load entries without an associated failure; that alone does not prove every
transition/marker works. Investigate relevant baseline compatibility before
shipping expanded reputation, equipment or other dependent adapters.

## Documentation branch verification

The documentation-only expansion branch was also checked with the full verifier,
using a separate `D:/GAMMAAPTools/plan-verification-runtime` so the running pilot's
runtime was not rewritten. Its unchanged foundation code passed 91 covered tests
and two real-server tests, with 100% owned Python line/branch coverage and 100%
executable-line coverage for its three non-generated Lua modules. These are the
foundation branch's counts; they do not replace the MCM branch's separate results
or verify planned expansion features.

## Earlier foundation evidence

### Baselines

The initial foundation record on 18 November 2026 observed the Anomaly 1.5.3
vanilla menu and GAMMA launcher v8.6 from the isolated directories. Installation
was still downloading at that point; the current environment above supersedes
that pending status.

After foundation development, the protected installation's 163,937-file baseline
has zero added, missing or size/timestamp-changed files and zero filesystem links.
All 859 backed-up appdata/profile files still match their original SHA-256, and
the backup copies also match. Detailed private inventories remain outside Git.

Archipelago reference: tag 0.6.8, commit
`54803be064fc7e80c4628777ed0b46a9390f255f`. Local Python: 3.12.3 on Windows.

The initial published documentation bootstrap `e467777` inherited the machine's
work author/committer email despite the local personal user setting. Local
`author` and `committer` overrides now explicitly use the requested personal
address, with commit/push checks. Global work settings and published history are
preserved. The private remote belongs to personal account `Lolager23`.

### Automated evidence

`tools/verify.py` passes locally with 91 regression/integration tests under coverage
and two additional real-server tests. The world generation regression checks
1,000 seeds. Every owned Python runtime module currently has 100% line and branch
coverage. The three non-generated Lua modules reach 100% executable-line coverage;
Lua branch coverage is not measured. These numbers describe this finite pilot,
not the finished randomiser's correctness or game compatibility.

The real server tests generate an actual seed, host upstream MultiServer on a
loopback websocket, authenticate the real CommonClient, send all checks, receive
items, report the goal and reconnect. Both solo and mixed APQuest sessions pass.
Game snapshots in these tests are synthetic; the Anomaly engine is not running.

Packages are rebuilt twice and compared byte-for-byte. The `.apworld` is loaded
in a separate process through upstream's archive loader, without a loose copy
of the GAMMA world. Generated catalogues and MO2 package contents are checked.

Regressions cover canonical protocol parsing, malformed/partial data, unknown IDs,
duplicate and conflicting histories, wrong seed, old-save rollback, failed item
creation, bounded polling, save/load callbacks, path escapes, hardlinks, symlinks
and junctions. Real-server testing found and fixed use of the optional seed filter
instead of `server_seed_name`. A separate reconnect regression prevents empty
connection state from truncating the previously accepted item history.

Upstream warns that its optional `_speedups` extension is absent; the supported
pure Python fallback is used. Real-server tests run without coverage tracing due
to the local Python/C-backed YAML interaction described in the development guide.

## Remaining acceptance

- The Windows/Linux workflow is active at `.github/workflows/verify.yml` after
  the user authorised the required GitHub `workflow` scope. Hosted run evidence
  is linked from [PR #1](https://github.com/Lolager23/gamma-archipelago/pull/1/checks);
  inspect the current head's results separately from the local results above.
- Independently verify the Cordon check, remaining Medkit and pilot completion.
- Controlled game save/reload, client/server restart, disconnect and wrong-session
  checks from the development guide, using disposable development saves.
- Verify transfer and player attribution in a live mixed-game multiworld.
- Measured crash/rollback recovery policy before MVP.
- Every expanded category, PDA message and alternate goal remains planned until
  implemented and accepted through the [expanded checklist](expansion-plan.md).

Foundation PR #1 was merged by the user's instruction. Callback-probe PR #2 and
MCM PR #3 remain draft at this observation. Later validation must identify its
actual source commit. No normal multiplayer saves are used, and no claim of
in-world multiplayer compatibility is made.
