# Expansion two: delivery and native acceptance

Source implementation is delivered as stacked **draft** PRs, starting at PDA
localization #38. Nothing in this stack is merged or deployed automatically.
The compatibility investigation #39 remains independent. Check the current PR
head's CI rather than importing a green result from its parent.

| Step | Draft PR | Implemented contract |
|---|---|---|
| 31 | [#40](https://github.com/Lolager23/gamma-archipelago/pull/40) | PDA tracker, regional/status filters and progression summary |
| 32 | [#41](https://github.com/Lolager23/gamma-archipelago/pull/41) | Scouting/shared hints, finite purchase/goodwill checks, next reward previews |
| 33 | [#42](https://github.com/Lolager23/gamma-archipelago/pull/42) | Distinct discovery quotas, exclusions and fragile-check policy |
| 34 | [#43](https://github.com/Lolager23/gamma-archipelago/pull/43) | Three progressive tool tiers and native action guards |
| 35 | [#44](https://github.com/Lolager23/gamma-archipelago/pull/44) | Repair/upgrade/craft permissions and four known-recipe groups |
| 36 | [#45](https://github.com/Lolager23/gamma-archipelago/pull/45) | Optional permission supplies, resumable delivery cursors and failure status |
| 37 | [#46](https://github.com/Lolager23/gamma-archipelago/pull/46) | Medical, maintenance, calibre-specific ammunition and expedition packages |
| 38 | [#47](https://github.com/Lolager23/gamma-archipelago/pull/47) | Capped additive carry capacity through GAMMA's keyed API |
| 39 | [#48](https://github.com/Lolager23/gamma-archipelago/pull/48) | Budget, protected openings, pacing settings, presets and generation reports |
| 40 | [#49](https://github.com/Lolager23/gamma-archipelago/pull/49) | Combined generation/server/recovery regressions and evidence reconciliation |

## Automation and limits

Each feature has deterministic regressions and the full verifier. Step 40 adds
168 combined filled seeds across scouting/spoiler policies, service exclusions,
discovery modes, supply calibres, attached supplies and carry rewards. This is a
bounded combination matrix, not exhaustive enumeration of every setting.
The existing 9,000 preset seeds, independent pacing/category/goal matrices and
malformed/session/order/path regressions remain enabled.

Actual upstream generation exercises gifts plus starting-from-pool tool depletion
in three real seed archives. It checks schema-4 session metadata, exact tool
copies, initial logic reachability, summary/spoiler separation and report packaging.
An additional two-GAMMA-plus-APQuest session receives initial items and every
network reward, saves/restarts the server and replays history after an older
synthetic acknowledgement. Synthetic game snapshots are not engine acceptance.

A combined LuaJIT test exercises tools, workshop/recipe permissions, medical
supplies and carry effects in one ordered history. It reloads a partial package,
preserves completed effects on normal reload, and reconciles permissions/carry
after rollback. Real older-save loading must also restore native inventory;
creating items and saving cannot form a crash-proof exactly-once transaction.

The Node UI regression checks labeled, bounded controls, quota enable/disable,
numeric/empty edits and preserved drafts. Browser checks on Step 39 exercised
live controls, exclusions, validation refusal and recovery. Numeric JavaScript
coverage and Lua branch coverage are not measured. Package/catalogue/localization
parity, archive loading, reproducible packaging, lint, typing and per-module
coverage gates stay enabled without exclusions or lowered thresholds.

The final complete local verifier passed **980 covered Python/Lua + 54 untraced
generator/server + seven Node tests: 1,041 total**. Owned Python runtime modules
reached 100% measured line and branch coverage; Lua reached 100% measured
executable-line coverage. Final-head Windows/Linux evidence is retained with each
PR; it must be checked again if that head changes.

Native APIs were inspected in the pinned baseline and active development overrides.
Workshop recipes still need ordinary knowledge/materials; permissions do not
unlock every book recipe. Carry capacity is the only newly shipped convenience
effect. Hints are AP LocationScouts/shared location hints, not paid `!hint`
commands. Shop checks are three named first purchases; goodwill has four finite
thresholds and does not claim a guaranteed trader-stock tier. Quotas count distinct
types, never repeated kills of the same type. Time estimates remain uncalibrated.

## Owen's native acceptance: not run

For each merged increment, first follow the development guide's verified full
appdata/profile/configuration backup and isolated deployment procedure. Keep the
local-only developer panel. Use matching world, companion and add-on revisions,
fresh Loner/Cordon development saves and MO2's **Archipelago DEV** profile.
These are future manual acceptance steps; this implementation task performs no
deployment, launch, save load or installed-game write.

| Area | Evidence to capture | Status |
|---|---|---|
| PDA | Tab layout/aspect ratios, other PDA tabs, filters, pagination, refresh, completed/available/blocked reasons and goal tracker | Not run |
| No-PDA | Bridge continues, protected PDA arrives before needing it, tab returns after acquisition/reload | Not run |
| Services/hints | Correct traders, paid purchase once, goodwill thresholds, recipient labels, local/shared hint privacy and next reward toggle | Not run |
| Discovery | First 15 distinct qualifying types, repeated types, exclusions, quota cap, save/reload and rollback | Not run |
| Tools/actions | Basic/advanced/expert repair/craft/upgrade guards, technician and self routes, ordinary tool acquisition and disabled-option behavior | Not run |
| Recipes | Four supported recipe groups, known/unknown native recipes, parts/tool requirements and conflicting overrides | Not run |
| Delivery | Partial supply failure, pending reason/cursor, normal reload, uncertain creation refusal and older-save consequences | Not run |
| Packages | Native sections/box quantities, chosen calibre, economy and unwanted-supply frequency | Not run |
| Convenience | +5/+10/+15 kg cap, other modifiers, new actor, reload and rollback | Not run |
| Opening/access | Fresh short/standard/extended openings, all transition routes, map keys, psi/quest gates and actual reachable settlements | Not run |
| Multiplayer | In-game attribution and delivery between GAMMA slots and another game, offline checks, reconnect and restart | Not run |
| Balance/release | Measured durations, grinding/rare encounter burden, deaths/waiting, install/upgrade/removal and independent human review | Not run |

Record source SHA, bundle hashes, baseline, seed/player/options, evidence and an
explicit passed/failed/blocked result. Failures become focused follow-up PRs with
reproducing regressions. The original pilot reload/third-map acceptance retains
its original evidence; it does not validate these additions or in-world multiplayer.

## Remaining work

- Complete the native matrix and calibrate short/standard/extended playtimes.
- Address compatibility or balance defects exposed by those runs; retain failing
  evidence and test the matching bundle after each fix.
- Complete the existing release gates: independent review, supported versions,
  migration/recovery policy, licensing, performance and checksums.
- Broader convenience effects, arbitrary shops/recipes and automatic encounter
  availability need separately scoped, verified adapters before becoming claims.

No numbered source feature remains intentionally deferred within Steps 31–40.
The unchecked native/release work above remains required before calling the
expanded randomiser accepted or releasing it publicly.
