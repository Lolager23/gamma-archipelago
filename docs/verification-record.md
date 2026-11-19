# Verification record

## PDA grammar and translation resources: 19 November 2026

Implemented English grammar and translation-ready whole-sentence game resources;
see [PDA notices](pda-reward-messages.md). A baseline reproducer confirmed the old
`a 100 Rupees` and forced player-possessive templates. Regressions now cover plural,
currency, acronym and arbitrary-name labels, game-selected translations, fallback,
resource parity, opaque placeholders, foreign item-ID collisions and legacy/v2
sidecars. Saved notice identities, receipt/check IDs and save schemas are unchanged.
Upgrade companion and add-on together for version 2 semantic presentation.

Full local verification **passed** using a separate tooling runtime: 772 covered
Python/Lua tests, 32 untraced generator/server tests and five Node tests, **809
total**, including the 6,000-preset seed matrix and actual AP server sessions.
Every owned Python runtime module measured 100% line and branch coverage; Lua
executable-line gates passed. Lua branch coverage is not measured. Reports and
package checksums remain outside source control and in CI artifacts.

The source branch builds on a separate test-fixture correction for Windows early
HTTP rejection races. Current-head Windows/Linux CI is a separate delivery gate.
Native PDA rendering, selected-language/font behavior and the in-game acceptance
list are **not run**, reserved for Owen. No game launch, deployment, installed
panel change or protected multiplayer write occurred.

## Sequential merge review: 19 November 2026

At Owen's explicit instruction, PRs #2–#35 were reviewed, fixed where required,
verified and merged individually in dependency order. PR #36 reconciles the
checklist and this audit. The [merge record](merge-review-record.md) lists each
reviewed head, merge commit, local counts and substantive fixes. Windows and
Ubuntu CI passed before each merge; an additional REST audit confirmed successful
check runs on all 34 recorded review heads. The final checklist uses the same gates.

The complete current verifier passes **719 covered Python/Lua + 32 untraced
generator/server + five Node tests: 756 total**. Every owned Python runtime module
measures 100% lines/branches; measured Lua executable lines pass their gates.
Lua branch and numeric JavaScript coverage are not measured. The seed matrix
retains 6,000 preset seeds, 231 category singles/pairs and 60 full-option goal
seeds. Real AP server/restart and web generation use actual upstream traffic and
seed archives, with synthetic game snapshots and mocked native APIs.

Review regressions cover exact signed-53-bit foreign notice IDs, skill retry
progress, story-key prerequisites, formerly failing zone fills, reused native
pickup flags, invalid travel vertices, settings-bound outgoing snapshots,
confirmed starting-money reductions and clearing stale client-owned notices.
Existing earlier regressions remain in the suite. The complete local logs,
review notes and exact-head audit are under `D:/GAMMAAPTools/merge-review`.

The actual private candidate at PR #34 review head `ec1f47e` rebuilt identically
twice; all 60 payload hashes/sizes and its exact source revision were verified.
Its manifest keeps engine acceptance not run and publication unapproved. This
is packaging evidence, not acceptance of a finished game.

No game was launched or loaded, no add-on was deployed, and no normal/development
game root, MO2 profile or save was changed during this merge pass. Existing
worktrees and the running local app were preserved; they do not automatically
update to merged main. Expanded engine acceptance and independent human release
review remain not run. The earlier pilot acceptance below remains valid on its
original evidence basis. Earlier sections retain their dated counts/observations;
they are superseded by this entry for current source and merge status.

## Generator extended QA and fixes: 19 November 2026

The full verifier passed **653 covered + 32 untraced Python/Lua tests**, plus
**five Node frontend regressions**: 690 tests total. All owned Python runtime
modules reached 100% measured lines and branches, and existing Lua executable-line
gates passed. Lua branch and numeric JavaScript coverage are not measured.

Browser testing reproduced No Starting Weapons permanently overwriting normal
firearms/melee choices. The fix preserves draft state separately from normalized
previews. On/off controls and a downloaded YAML now restore the original modes.
Pending/invalid edits clear old totals. Reserved player names now block downloads,
and exported names match upstream trimming. Incomplete JSON bodies are refused;
timeouts and nesting limits return bounded errors. Brackets/escapes in strings
remain valid. A backend-stop test also found a stale connected banner, now fixed;
restart plus another edit recovered the existing draft and generation controls.

All six presets passed browser count checks. Six presets times two boundary
seeds generated exact preview IDs, reward IDs and settings. Three repeated-seed
cases reproduced placements/settings. Two actual concurrent HTTP requests
produced one seed and one busy refusal; a later request succeeded. The complete
suite also retains 6,000 preset seeds, category/goal matrices, ten real-server
cases, packaged-client/APWorld loading and reproducible-package checks.

A browser download using the maximum 64-bit seed succeeded. Search/no-match,
custom/duplicate milestones, invalid seed/name controls, lock restoration and
server recovery were exercised. Private logs are under `D:/GAMMAAPTools` as
`web-qa-reproductions.log`, `web-qa-real-generation.log` and
`web-qa-full-verification.log`; the browser image is
`diagnostics/generator-qa.jpg`. No game launch, save change, mod deployment,
merge or public/hosted publication occurred. The app remains local-only.

## Generator web app: 19 November 2026

The complete verifier passed with 645 covered tests and 17 untraced
generation/server tests: **662 passed**. All owned Python runtime modules,
including the four web modules, reached 100% measured line and branch coverage.
Existing Lua executable-line gates still passed; Lua branch coverage is not
measured. JavaScript module syntax checks now run in the verifier as well.

The additional integration case generated and inspected a real downloadable AP
seed ZIP. In browser checks, the full preset displayed 257 checks / 87 eligible
reward types; invalid zone settings and duplicate milestone thresholds blocked
generation. Starting-lock controls, reward search, calculator keyboard input,
actual seed ZIP download and actual YAML download were exercised. No browser
console errors/warnings were observed. The narrow layout had no page overflow;
the roster table retains its own horizontal scroll. This is manual browser
evidence, not numeric JavaScript coverage or GAMMA engine acceptance.

The web generation runtime and session storage use separate tooling directories.
The local verifier log is `D:/GAMMAAPTools/web-generator-verification.log`.
No game launch, save changes, deployment, server start or merge occurred.
See the [workbench guide](generator-web-app.md) for setup and estimate limits.

## Expanded candidate automation: 19 November 2026

Step 30's complete local verifier passed on Windows with Python 3.12.3 and the
pinned Archipelago 0.6.8 runtime. It ran 592 covered tests and 16 untraced
generation/server tests: 608 passed. Every owned Python runtime module reached
100% line and branch coverage; every measured non-generated Lua module reached
100% executable-line coverage. Lua branch coverage is not measured.

The generation matrix ran 1,000 seeds for each of six presets, alongside category
and goal combinations. Ten actual loopback-server cases exercised the companion
and expanded mixed-game/recovery paths with synthetic game snapshots. Lint,
formatting, typing, catalogue parity, reproducible packages, portable companion
loading and upstream APWorld archive loading also passed.

The verifier used `D:/GAMMAAPTools/stack-verification-runtime`; the private local
log is `D:/GAMMAAPTools/release-step-verification.log`. Current-head Windows/Linux
CI is linked from [PR #34](https://github.com/Lolager23/gamma-archipelago/pull/34/checks).
Check that head's results separately from this local evidence.

All thirty increments now have implementation PRs in the
[index](implementation-status.md). No expanded engine acceptance was run: Owen
explicitly reserved that work for after each merge and requested no further
automated game launches. Older observations below remain dated pilot evidence.
The [v1 checklist](version-one-release.md) records the remaining acceptance gates.

## Acceptance update: 19 November 2026

The user confirmed game reloading and third-map validation. On follow-up, the
user explicitly accepted the third-map trigger on the basis that it shares the
working trigger code and instructed that it be marked complete. Ordinary game
save/reload and third-map acceptance are therefore closed by user confirmation.

This is an acceptance decision, not a new captured Cordon server event. The
available server log still records Garbage/Rostok and two awards; the latest
game snapshot reports two applied items. No Cordon/Medkit or pilot-goal packet
was independently captured in this update. Preserve that distinction when
reporting observed results. Older-save rollback, client/server restart, network
recovery and wrong-session tests remain separate acceptance cases.

## Live pilot observation: 18 November 2026, 23:34 UTC

The user reported that the triggers and rewards work. Independently inspected
the current local server log, its persisted `.apsave`, the game log and both
bridge snapshots. The deployed source is `a7995ef` on the MCM branch; these
observations do not imply that this documentation branch implements that PR.

| Check | Server confirmation | Game application evidence |
|---|---|---|
| Rostok: First Arrival, ID 28052003 | One recorded Bandage award; present in persisted server checks | Game log records `Received bandage`; acknowledged receipt history includes item 28051003 |
| Garbage: First Arrival, ID 28052002 | One recorded Basic Toolkit award; present in persisted server checks | Game log records `Received itm_basickit`; acknowledged receipt history includes item 28051001 |
| Cordon: First Arrival, ID 28052001 | Not present in the inspected server check set | Third-map acceptance closed by the user on 19 November based on shared trigger code; no independent Cordon capture |

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

## Earlier foundation acceptance backlog (historical)

The callback-probe increment has its own [source findings and evidence matrix](callback-probes.md).
Its local verifier passes 140 covered tests plus two real-server tests, with 100%
Python line/branch coverage and 100% executable-line coverage for the five owned
Lua modules. This remains automated evidence; no callback-probe in-game acceptance
has been marked passed.

- The Windows/Linux workflow is active at `.github/workflows/verify.yml` after
  the user authorised the required GitHub `workflow` scope. Hosted run evidence
  is linked from [PR #1](https://github.com/Lolager23/gamma-archipelago/pull/1/checks);
  inspect the current head's results separately from the local results above.
- Ordinary game save/reload and third-map acceptance are complete by user
  confirmation; see the acceptance update above for the evidence basis.
- Independently capture the remaining Medkit delivery and pilot completion.
- Older-save rollback, client/server restart, disconnect and wrong-session checks
  from the development guide, using disposable development saves.
- Verify transfer and player attribution in a live mixed-game multiworld.
- Measured crash/rollback recovery policy before MVP.
- Every expanded category, PDA message and alternate goal remains planned until
  implemented and accepted through the [expanded checklist](expansion-plan.md).

At that foundation observation, PR #1 was merged by the user's instruction while
callback-probe PR #2 and MCM PR #3 were drafts. Later validation must identify its
actual source commit. No normal multiplayer saves are used, and no claim of
in-world multiplayer compatibility is made.
