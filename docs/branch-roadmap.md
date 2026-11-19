# Branch-by-branch work

The [second expansion stack](expansion-two-plan.md) adds Steps 31–40 after the
original thirty increments, starting on `codex/pda-tracker` from PDA localization
PR #38. Its table defines the new dependencies and acceptance contracts.
The [delivery and acceptance index](expansion-two-acceptance.md) links implemented
drafts and records the remaining manual game and release gates.

Implementation update: the [PR/status index](implementation-status.md) records the
thirty merged implementation steps and remaining engine acceptance. Owen later
explicitly authorized sequential review/fixes/merges, completed for PRs #2–#35;
PR #36 reconciles this status. See the [merge audit](merge-review-record.md).
The planning text below is retained as the original specification and milestone
history, including its earlier prohibition on unrequested merges. Public release
and native acceptance remain separate decisions.

On 19 November 2026 the user authorised implementing this roadmap as a PR stack:
each numbered step gets its own branch/PR based on the preceding step. Existing
prerequisites are stacked as PR #3 (MCM) → PR #4 (plan), preserving history.
Each implementation PR records its preceding PR, automated results and remaining
live acceptance. Draft status does not imply completion. Do not merge or release
the stack automatically.

The user subsequently reserved live game verification for themselves after each
merge. Do not launch/load GAMMA automatically; implement the full stack with
source-backed adapters, automated checks and explicit not-run engine acceptance.

Each branch includes tests and documentation for its
own behaviour. The [expanded checklist](expansion-plan.md) defines category
options, exact proposed triggers, rewards, notification wording and exit criteria.
The rows below are PR-sized increments; they are not completed implementations.

## Existing work

| Branch | Recorded state on 18 November 2026 |
|---|---|
| `codex/archipelago-integration` | Foundation merged through PR #1. Three-check pilot exists. |
| `codex/game-callback-probes` | Draft PR #2; inspect its actual evidence and remaining probes before merging. |
| `codex/archipelago-mcm` | Draft PR #3; menu/button and ordinary reload confirmed by the user. Live server/game evidence confirms two pilot checks/rewards; third-map acceptance closed by the user on 19 November based on shared trigger code. |
| `codex/expanded-randomiser-plan` | Documentation and verification only; no category, goal or notification implementation. |

Do not merge these branches implicitly. Notifications depend on the foundation;
MCM controls additionally depend on PR #3. Probe findings can inform later work
without importing every experimental script into the shipped add-on.

## Planned increments

| Order | Branch | Deliverable and acceptance |
|---|---|---|
| 01 | `codex/pilot-acceptance` | Stage 0: third-map trigger and ordinary reload accepted by the user. Remaining work: capture third reward/goal, older-save recovery and reconnect; distinguish acceptance from captured evidence. |
| 02 | `codex/content-hook-inventory` | Stage 0: finite map/settlement/species/faction/artefact/task/equipment/rank/lab rosters; callback arguments and active mod winners. Reuse reviewed PR #2 findings. |
| 03 | `codex/pda-reward-messages` | Stage 1: versioned sender/recipient metadata, applied-reward notices and server-confirmed outgoing notices; self-transfer deduplication and real mixed-game proof. |
| 04 | `codex/session-recovery` | Stage 1: durable checks, ordered receipts, notification cursors, AP server restart and measured save/rollback policy for each reward kind. |
| 05 | `codex/category-options` | Stage 2: independent check/reward options, goal choice, preset YAML, slot manifest, invalid combination and pool-size validation. Unsupported options fail clearly. |
| 06 | `codex/starting-loadout-options` | Stage 2: independent initial equipment/supply omissions, No Starting Weapons preset, faction/custom-loadout handling and initialization before AP rewards; later earned gear survives reload. |
| 07 | `codex/all-map-checks` | Stage 2: every supported map; preserve pilot IDs, use real regions and test actual level identifiers. |
| 08 | `codex/settlement-checks` | Stage 2: every major hub's verified entry volume, no duplicate checks on overlap/load/re-entry. |
| 09 | `codex/combat-checks` | Stage 3: separate first-mutant/first-faction options and bounded kill totals; actor attribution, victim identity and save/reload tests. |
| 10 | `codex/artefact-checks` | Stage 3: every supported artefact type, canonical variants and acquisition provenance; no drop/pickup farm. |
| 11 | `codex/task-checks` | Stage 3: quest types, bounded side-task totals and story milestones; completion/failure/cancellation and task-instance deduplication. |
| 12 | `codex/equipment-checks` | Stage 3: separate upgrade, armour, weapon and knife options with explicit tier manifests and actual equip/upgrade evidence. |
| 13 | `codex/rank-checks` | Stage 3: active rank thresholds, monotonic milestones and downgrade/load regressions. |
| 14 | `codex/loot-stash-rewards` | Stage 4: white coordinates, finite quality/calibre loot tables, stable contents and one-claim recovery. |
| 15 | `codex/progression-stash-rewards` | Stage 4: orange coordinates, guaranteed progression contents and world rules for local stash claims. |
| 16 | `codex/reputation-rewards` | Stage 4: bounded faction bonuses and actual trader-tier eligibility; no forced hostility/alliance changes. |
| 17 | `codex/skill-level-rewards` | Stage 4: supported Haruka/GAMMA adapter, caps, recalculation and saved levels; absent/incompatible mod refusal. |
| 18 | `codex/quest-progression-keys` | Stage 5: persistent quest permissions, ordinary-source replacement and matching world/game prerequisites. |
| 19 | `codex/starting-gear-unlocks` | Stage 5: optional AP-locked detector/PDA/weapons/other durable gear, seventh reward toggle, usable baseline grants, pending PDA messages and no self-locks; combined restricted-start tests. |
| 20 | `codex/zone-access-keys` | Stage 5: every normal/extra/scripted route, safe starting access, return paths and no self-locks. |
| 21 | `codex/zone-unlock-travel` | Stage 5: one optional safe-settlement trip per unlock, persistent consumption and protection/hostile-hub checks. |
| 22 | `codex/goal-psi-protection` | Stage 6: qualifying usable protection, calibration and access prerequisites; actual completion packet. |
| 23 | `codex/goal-brain-scorcher` | Stage 6: verified shutdown state and game/solver prerequisites. |
| 24 | `codex/goal-meet-strelok` | Stage 6: canonical encounter completion, distinct from Living Legend completion. |
| 25 | `codex/goal-living-legend` | Stage 6: terminal chain event, task/NPC prerequisites and supported faction/start rules. |
| 26 | `codex/goal-all-x-labs` | Stage 6: frozen lab roster, actual entry checks and reachability/protection. |
| 27 | `codex/configuration-and-balance` | Stage 7: individual/pairwise/full presets, 1,000 seeds per preset, adversarial gate/goal combinations and no impossible item pools. |
| 28 | `codex/multiworld-acceptance` | Stage 7: two fresh MVP runs, one successful run per goal, real mixed-game transfers and all recovery/notification cases. |
| 29 | `codex/release-hardening` | Stage 7: compatibility, performance, migration, clean install/uninstall, independent review, docs and licence audit. |
| 30 | `codex/version-one-release` | Supported requested categories/goals, reproducible packages, checksums, tagged release and maintenance guide. Explicit release approval required. |

For this authorised implementation stack, start each branch from the preceding
step and target that branch in its PR. Name the dependency and preserve published
history. Retarget after merges when instructed; do not mix a new feature into an
existing unrelated PR. Stash, reputation and skill
work have separate adapters but still use the same receipt/state authority.

If an increment becomes too large, split it by observable behaviour and update
this table. Every feature branch includes its own option tests and live acceptance;
the final matrix does not postpone basic validation until the end. No automatic
merges or public releases.

Transition shuffling, equipment licences beyond these rewards, traps/DeathLink
and xrRazom co-op remain separate exploratory branches after the supported scope.
They must not delay or silently replace the requested checks, rewards and goals.
