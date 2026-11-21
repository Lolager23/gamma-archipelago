# Verification record

## 21 November 2026 — generic discovery tails and seeded starting permission

Added configurable filler-only final mutant/artefact quota checks, pre-fill budget
and placement guards, an optional seeded starting PDA/Firearms/Detector permission,
and matching PDA requirements for quest/task/story checks in AP logic and the PDA.
Existing generic checks remain first-N distinct types; published IDs and zero-default
wire/digest identities are unchanged. New seed options need fresh generation.
Exact-head local/Windows/Linux verification and package evidence are retained with
the implementation PR. Native acceptance is **not run**, reserved for Owen; the
normal game and active playtest are excluded from source verification.


## AP playthrough guards: 21 November 2026

New APWorld starts are restricted to Free Stalkers and the three native presets,
with seed-fixed Random selection and matching world/key routing. Native purchase
validation now precedes transfers/debits. Accepted silent transition denials prefer
inverse-route arrivals and reject full ALife/extra transition bounds, including
unregistered/overlapping triggers. See [implementation and acceptance](ap-playthrough-guards.md).
Regression/generation/server/current-head CI evidence is on the PR. Native
acceptance is **not run**, reserved for Owen. Existing saves/seed bindings are retained.

## Quick Sidorovich pilot: 20 November 2026

The named pilot preset selects the additive `talk_sidorovich` goal (6). Closing
Sidorovich's native dialogue in Cordon completes the goal while other map checks
remain available. Existing goal IDs, legacy defaults and current seeds are
unchanged. See [quick pilot](pilot-sidorovich.md) for trigger/release policy and
acceptance. Automated evidence is recorded on the PR; native acceptance is
**not run** and reserved for Owen. The current Brain Scorcher session is preserved.

## Buyable AP shop contracts: 20 November 2026

Branch `codex/shop-purchases` adds the default-off `checks_shop_purchases` option
and nine new IDs, retaining the older ordinary-purchase checks unchanged. The
docked native trader page uses descriptive contracts, exact prices, the credited
official icon and scouted reward/recipient data only when enabled and known.
The catalogue remains authoritative; the web workbench exposes the toggle,
selected prices and currency budget. Existing default configuration identities
remain unchanged. New checks require a new seed and matching fresh Dev character.

A backward-compatibility regression also reproduces the previous add-on refusing
an unknown new option even when zero. The encoder now omits only that disabled
wire record; enabled shops still advertise it and require the matching add-on.

Regressions cover payment once, affordability, wrong trader/session/configuration,
receipt-history conflicts, confirmed-check recovery, offline writes, uncertain
payment persistence, save migration/refusal, hidden scouting, native delegation,
bounded refresh, live cash changes and clipped long-text scrolling. The full
verifier and current-head Windows/Linux evidence are recorded on the PR. An
independent Windows image decoder reproduced all 4,096 generated icon pixels.

Native acceptance is **not run**, reserved for Owen. No game launch or current
Brain Scorcher reset is part of this increment. See the [acceptance checklist](shop-purchases.md).

## Empty stash interaction and rainbow markers: 20 November 2026

Owen reported empty AP stashes. The old adapter marks the box opened but waits
for its 500 ms poll to create contents; the active GAMMA inventory refreshes its
loot contents on the next UI frame. Two retained regressions fail against that
implementation: opening without an actor update, and reopening a legacy saved
pending plan. The correction fills during use, keeps the existing action identities
and bounded retry path, and counts actual claims instead of opens in the tracker.
Failed protected-helmet creation also restores its prior permission, and refused
saves cannot create loot through the interaction path.

Both AP stash kinds now reference an original rainbow backpack DDS through an
additive texture descriptor. The descriptor loader and resource lookup were
checked against pinned Monolith `7289a03` (`MainMenu.cpp` and `UITextureMaster.cpp`).
The generated texture was inspected at full size and downsampled to 12px; that
preview is artwork evidence, not an in-game capture. Packaging permits only the
exact regenerated binary icon and still rejects foreign assets and links.

The complete verifier, coverage and current-head Windows/Linux results are
recorded on the PR. Native stash opening, rainbow rendering and current-save
recovery remain **not run**, for Owen. No new seed or character is required;
already-recorded created objects are never inferred missing and replaced.

## Tracker clarity and reverse navigation: 20 November 2026

Branch `codex/tracker-redesign` replaces the dense mixed checklist/progression
columns with separate Checks/Progression pages and a shared goal/count header.
Checks are directly selectable native list rows with contextual requirements,
scouting and reward recipients. Region/status filters support backward right-click
navigation through the engine's actual `OnMouse` extension; ordinary button events
alone do not deliver right-click. Default available checks, explicit empty states,
disabled page-edge actions and named highest rank reduce ambiguous controls.

Regressions cover reverse/wrapping navigation, mouse delegation/hit boundaries,
hidden/disabled controls, direct selection and its location ID across live updates,
cleared stale feedback, empty/unbound views, long text, independent viewports,
refresh caching, scroll preservation and garbage collection before native-model
updates. Layout contracts account for mutually exclusive page bodies and retain
the original native-tab clearance and userdata-lifetime regressions. The full
verifier and exact-head Windows/Linux results are recorded on the PR.

Native acceptance is **not run**, reserved for Owen. No game launch, seed reset,
progression/receipt mutation, APWorld/client change or save-format migration is
part of the redesign. Any diagram/preview is synthetic layout evidence only.

## Locked-zone loading loop: 20 November 2026

Owen's attempted locked-Agroprom trip **failed** in GAMMA Dev. The retained private
log shows repeated transition inspection failures followed by denied packets,
same-zone autosaves and reloads. The class helper was incorrectly named
`IsLevelChanger`; the extracted baseline exports `isLc` and native class IDs.
The late void packet hook reused the actor's position inside the trigger. Pinned
Monolith `alife_update_manager.cpp`, `level_changer.cpp` and `UIGameSP.cpp` confirm
that the hook cannot cancel loading, and silent changers bypass the enabled flag.

Branch `codex/fix-locked-zone-loop` uses class IDs, guards native spawn/scripted
entry points, and redirects an already accepted denied packet to a graph point
outside transition volumes in the source map. No cached pre-save position or
save-format change is needed. Tests model the silent-trigger reload cycle,
an existing trigger-position save, normal disables/unlock ownership, extra-mod
side effects, delayed calls, unknown targets and delegate composition. The
no-recovery-point case reports that an earlier save is required, rather than
repeating an unsafe packet. Full verifier and current-head Windows/Linux CI
results belong on the PR; focused runs do not meet the complete coverage gate.

The stuck development process was closed with Owen's permission. Before changes
to installed files, 1,442 private backup files were copied and SHA-256 verified;
the current server recorded eight checks and eight rewards. Do not reset the
session or replace its saves. Native verification of the fix is **not run**,
reserved for Owen; no automatic game launch is permitted. See
[zone access keys](zone-access-keys.md) for the remaining recovery limitations.

## Source-check causes in PDA announcements: 19 November 2026

Branch `codex/pda-check-announcements` adds the earning check to the end of sent
and received notices. It uses the authenticated source slot's game/location,
catalogue-backed action wording for GAMMA and data-package labels for other
games. Starting/server items retain an honest source label. It distinguishes
hostile totals, first kills and distinct-type quotas.

Regressions exercise every published GAMMA check, all cause templates/directions,
foreign ID collisions, metadata arriving after receipts, self-award deduplication,
malformed sidecars, translation fallback/value labels, literal placeholders,
version-1/2 compatibility and version-3 mixed batches. A save/load case preserves
seen identities, waits for loading dismissal and applies only the new receipt.
Complete verifier/current-head CI results and package hashes are recorded on the
PR; focused subsets do not satisfy the complete coverage gate by themselves.

Native verification is **not run**, reserved for Owen. This is presentation-only:
no published ID, generation rule, seed/configuration identity or save/receipt
schema changes. Matching companion and game files are required for version 3.
Keep the current AP server/seed and saved progress when upgrading the companion;
do not replay old notices to add their newly available cause.

## Tracker opening crash / native row lifetime: 19 November 2026

Owen reported a native crash on opening the AP tab after the layout deployment.
The private DEV log reaches the base native `Update` call in `gamma_ap_pda`.
Source inspection found Lua-created checklist rows passed to a non-adopting
scroll binding; native auto-deletion does not transfer their Lua ownership.
Use the native XML static factory for row containers instead.

Two new regressions **failed** before the correction, after actual Lua collection
and modeled native child traversal. Both pass after it, along with the existing
16 tracker UI/layout cases. The fixture models distinct Lua handles and native
pointers rather than treating native parentage as a strong Lua reference.
Complete verifier/current-head CI results and package checksums belong to the PR
evidence; a focused subset alone does not satisfy the project coverage gate.

Native re-verification is **not run**, reserved for Owen. The change is limited to
UI row construction and leaves the current seed, checks, reward history, receipt
order, saved fields and developer panel unchanged. Crash logs, save names and
runtime inventories remain outside Git.

## PDA tracker formatting and tab clearance: 19 November 2026

Branch `codex/pda-tracker-layout` fixes the reported concatenated checklist and
progression entries and summary overlap with the native tabs. Four regressions
reproduced ordinary LF characters reaching the native text parser and the
summary intersecting the tab band at the modeled 4:3, 16:9 and 21:9 scales.

The page now uses explicit Status/Region/Check cells, measured reason/reward
lines, and independent scroll viewports for summary, checks and progression.
It converts line breaks to the native marker and starts below the background-
relative navigation band. Additional XML-driven boundary tests cover long labels,
CR/LF conversion, increasing row heights, non-overlapping viewports/buttons,
scroll retention, unchanged-refresh caching, multiline cache boundaries and
clearing stale views. The model uses fixed glyph widths; it does not measure the
native renderer, fonts or live aspect-ratio transformations.

The complete local verifier **passed**: 1,048 covered Python/Lua tests, 57
untraced generator/server tests and seven Node tests (**1,112 total**), including
the 9,000-preset seed matrix and actual APWorld loading. Owned Python modules
measured 100% lines/branches, and all measured Lua executable lines reached 100%.
Lua branch coverage is not measured. Current-head Windows/Linux results and
retained package hashes belong to this PR's evidence.

Native layout/scroll/font acceptance is **not run**, reserved for Owen. No game
was launched, installed files deployed, private developer panel changed or
running AP session restarted. No gameplay rules, IDs or save/bridge schemas
changed. This section records the isolated fix before integration with PRs #51
and #52; combined-head evidence is recorded in the PR.

## Stash marker crash correction: 19 November 2026

Branch `codex/fix-stash-marker-crash` isolates the reported `gamma_ap_loot`
missing-node assertion from the separate notice-timing work. Two new regressions
**failed** against main: querying the DXML document root skipped insertion, and
a registered-but-unready hook still allowed a native marker call. The corrected
patch verifies all four definitions and gates both new receipts and saved plans.

The complete verifier **passed** 1,051 covered Python/Lua tests, 57 untraced
generator/server tests and seven Node tests (1,115 total). This includes 568 Lua
tests, 100% measured Python lines/branches and 100% owned Lua executable lines.
Lua branch coverage is not measured. A separate standalone LuaJIT probe using
the inspected installed DXML and SLAXML parsers also **passed** root selection,
all four definitions, idempotence and native-node preservation; engine globals
were stubbed and no game was launched. Current-head Windows/Linux CI results are
recorded in the PR; native kill/reward/marker acceptance remains **not run**. This source-only
increment does not deploy, launch the game or alter the current AP session,
saves, local developer panel or normal installation.

## Defer AP popups until the world is visible: 19 November 2026

Branch `codex/defer-notices-until-world-ready` fixes the reported received/sent
reward and join popups appearing during loading. Two reproducing regressions
failed on `6b73c5a`: a living actor with precaching active, and a living actor at
the entry prompt even with zero precache frames. Both displayed all three kinds
of message before screen dismissal.

One transient presentation gate now waits for native dismissal, a later device
frame, zero precache frames, an unpaused device and a living actor in a present
level. Loading state and notice acknowledgements remain separate from receipt
application. Mocked-engine regressions cover both loading stages, same-frame
dismissal, failed/missing native APIs, pause/actor/level/precache conditions,
new-game/load/prompt/destroy resets, deferred display, saved identities and no
repeated rewards. The all-Lua pass completed **572 tests**, with 100% measured
executable lines; Lua branch coverage is not measured.

The complete local verifier **passed**: 1,055 covered Python/Lua tests, 57
untraced generator/server tests and seven Node tests (**1,119 total**), including
the 9,000-preset seed matrix. Every owned Python module measured 100% lines and
branches; all measured Lua executable lines reached 100%. Current-head
Windows/Linux checks and retained package evidence are recorded with the PR.
In-game acceptance is **not run**: Owen still needs to hold
the entry screen open while rewards arrive, dismiss it and check one-time popup
delivery, then repeat after reload/transition and with keypress loading disabled.
No game was launched, installed code deployed, session restarted or private
developer panel changed for this source fix. No IDs, bridge or save schemas
changed; already-displayed history remains intact.

## Startup join notices: 19 November 2026

Branch `codex/startup-notifications` adds an optional authenticated-player
startup/reconnect PDA message, based on reviewed main `2efe9ce`. The complete
`tools/verify.py` run with a separate pinned AP 0.6.8 tooling runtime **passed**:
1,036 covered Python/Lua tests, 57 untraced generation/server tests and seven
Node tests. Python line/branch coverage is 100%; the new Lua presence module has
100% executable-line coverage. Lua branch coverage is not measured.

Actual solo and mixed-game AP connections publish the correct slot name and a
new epoch on reconnect. Mocked-engine tests cover live-heartbeat requirements,
stale/duplicate/outdated snapshots, wrong session/configuration, localization
fallback, literal placeholders in names, save/load, clock rollback and failed
display/file operations without blocking item/check handling. The follow-up
removes PDA ownership gates from both join and transfer broadcasts; regression
tests reproduce the original suppression with omitted and AP-locked PDAs, then
check broadcast delivery, save/load deduplication and no replay on PDA acquisition.
The optional sidecar adds no save-schema or item/check protocol changes.

Native PDA startup/reconnect rendering is **not run**, and this branch is **not
deployed**. Hosted checks must be evaluated for its current PR head separately.
The source work uses an isolated worktree and verification runtime; it does not
alter either game installation, the existing local developer panel or local
third-party compatibility overrides.

## Second expansion source stack: 19 November 2026

Steps 31–40 implement the requested tracker, regional/progression displays,
scouting/shared hints, finite shop/goodwill checks, distinct discovery quotas,
tool/workshop/known-recipe permissions, resumable permission supplies, four supply
package categories, capped carry capacity, progression budgets, opening protection
and independent pacing settings. See the [stack and native matrix](expansion-two-acceptance.md)
and [plan](expansion-two-plan.md). The initial implementation was an **unmerged
draft stack** on PDA localization #38, with compatibility investigation #39
independent. The subsequent [user-authorized merge review](expansion-two-merge-review.md)
records source validation, fixes and canonical PR outcomes separately.

The original implementation verifier **passed** in its separate tooling runtime: **980
covered Python/Lua, 54 untraced generator/server and seven Node tests, 1,041 total**.
Owned Python runtime modules reached 100% measured lines/branches and Lua reached
100% measured executable lines. Lua branch and numeric JavaScript coverage are
not measured. The suite retains 9,000 preset seeds, category/goal/pacing matrices,
168 additional combined seeds, actual APWorld archive loading, reproducible
packaging and real server sessions. Each PR's final-head Windows/Linux evidence
and downloaded CI package checksums are retained separately under
`D:/GAMMAAPTools/diagnostics/expansion-two`.

New actual-generation regressions verify gifts and starting-from-pool depletion,
schema-4 identity, report packaging and explicit placement spoilers. Combined
two-GAMMA/APQuest traffic exercises initial items, every check/reward, server
save/restart and older synthetic acknowledgement replay. A combined LuaJIT test
resumes a partial package, preserves normal reload effects and rolls back
permissions/carry. These use synthetic game snapshots or mocked native APIs.
Browser checks exercised the new local controls, exclusions, invalid-configuration
refusal and recovery. No native game acceptance is inferred from those results.

Native verification, playtime calibration and release acceptance are **not run**,
reserved for Owen. No game was launched or loaded; no installation, profile,
save, deployed companion/APWorld, running user AP session or local-only developer
panel was changed. Protected normal game roots were untouched. The original
checkout and existing user work were preserved; implementation lives in isolated
source worktrees and the stacked branches. That initial implementation task did
not merge PRs or publish a release; the later authorized merge pass is separate.

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

**19 November source follow-up:** see the
[compatibility investigation](gamma-compatibility-investigation.md). The newer
00:35 UTC log contains none of the four historical signatures. Read-only source
inspection still finds three enabled consumers without enabled loose providers,
two providers installed in disabled optional mods, and a reproducible LuaJIT syntax
failure in the zoom script. No third-party repair or new native verification was
performed. The differing PDA bindings remain configuration dependent.

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

An earlier inspected game log contained four distinct third-party script failures
(the 19 November follow-up above supersedes its claim to be the latest log):

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
