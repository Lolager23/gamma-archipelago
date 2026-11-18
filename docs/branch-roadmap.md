# Branch-by-branch work

Branches are sequential by default. Each includes tests and documentation for its
own behaviour. The [expanded checklist](expansion-plan.md) defines category
options, exact proposed triggers, rewards, notification wording and exit criteria.
The rows below are PR-sized increments; they are not completed implementations.

## Existing work

| Branch | Recorded state on 18 November 2026 |
|---|---|
| `codex/archipelago-integration` | Foundation merged through PR #1. Three-check pilot exists. |
| `codex/game-callback-probes` | Draft PR #2; inspect its actual evidence and remaining probes before merging. |
| `codex/archipelago-mcm` | Draft PR #3; deployed menu/button confirmed by the user. Live server/game evidence confirms two pilot checks/rewards. |
| `codex/expanded-randomiser-plan` | Documentation and verification only; no category, goal or notification implementation. |

Do not merge these branches implicitly. Notifications depend on the foundation;
MCM controls additionally depend on PR #3. Probe findings can inform later work
without importing every experimental script into the shipped add-on.

## Planned increments

| Order | Branch | Deliverable and acceptance |
|---|---|---|
| 01 | `codex/pilot-acceptance` | Stage 0: third check/reward, actual goal, controlled save/load and reconnect; record failures honestly. |
| 02 | `codex/content-hook-inventory` | Stage 0: finite map/settlement/species/faction/artefact/task/equipment/rank/lab rosters; callback arguments and active mod winners. Reuse reviewed PR #2 findings. |
| 03 | `codex/pda-reward-messages` | Stage 1: versioned sender/recipient metadata, applied-reward notices and server-confirmed outgoing notices; self-transfer deduplication and real mixed-game proof. |
| 04 | `codex/session-recovery` | Stage 1: durable checks, ordered receipts, notification cursors, AP server restart and measured save/rollback policy for each reward kind. |
| 05 | `codex/category-options` | Stage 2: independent check/reward options, goal choice, preset YAML, slot manifest, invalid combination and pool-size validation. Unsupported options fail clearly. |
| 06 | `codex/all-map-checks` | Stage 2: every supported map; preserve pilot IDs, use real regions and test actual level identifiers. |
| 07 | `codex/settlement-checks` | Stage 2: every major hub's verified entry volume, no duplicate checks on overlap/load/re-entry. |
| 08 | `codex/combat-checks` | Stage 3: separate first-mutant/first-faction options and bounded kill totals; actor attribution, victim identity and save/reload tests. |
| 09 | `codex/artefact-checks` | Stage 3: every supported artefact type, canonical variants and acquisition provenance; no drop/pickup farm. |
| 10 | `codex/task-checks` | Stage 3: quest types, bounded side-task totals and story milestones; completion/failure/cancellation and task-instance deduplication. |
| 11 | `codex/equipment-checks` | Stage 3: separate upgrade, armour, weapon and knife options with explicit tier manifests and actual equip/upgrade evidence. |
| 12 | `codex/rank-checks` | Stage 3: active rank thresholds, monotonic milestones and downgrade/load regressions. |
| 13 | `codex/loot-stash-rewards` | Stage 4: white coordinates, finite quality/calibre loot tables, stable contents and one-claim recovery. |
| 14 | `codex/progression-stash-rewards` | Stage 4: orange coordinates, guaranteed progression contents and world rules for local stash claims. |
| 15 | `codex/reputation-rewards` | Stage 4: bounded faction bonuses and actual trader-tier eligibility; no forced hostility/alliance changes. |
| 16 | `codex/skill-level-rewards` | Stage 4: supported Haruka/GAMMA adapter, caps, recalculation and saved levels; absent/incompatible mod refusal. |
| 17 | `codex/quest-progression-keys` | Stage 5: persistent quest permissions, ordinary-source replacement and matching world/game prerequisites. |
| 18 | `codex/zone-access-keys` | Stage 5: every normal/extra/scripted route, safe starting access, return paths and no self-locks. |
| 19 | `codex/zone-unlock-travel` | Stage 5: one optional safe-settlement trip per unlock, persistent consumption and protection/hostile-hub checks. |
| 20 | `codex/goal-psi-protection` | Stage 6: qualifying usable protection, calibration and access prerequisites; actual completion packet. |
| 21 | `codex/goal-brain-scorcher` | Stage 6: verified shutdown state and game/solver prerequisites. |
| 22 | `codex/goal-meet-strelok` | Stage 6: canonical encounter completion, distinct from Living Legend completion. |
| 23 | `codex/goal-living-legend` | Stage 6: terminal chain event, task/NPC prerequisites and supported faction/start rules. |
| 24 | `codex/goal-all-x-labs` | Stage 6: frozen lab roster, actual entry checks and reachability/protection. |
| 25 | `codex/configuration-and-balance` | Stage 7: individual/pairwise/full presets, 1,000 seeds per preset, adversarial gate/goal combinations and no impossible item pools. |
| 26 | `codex/multiworld-acceptance` | Stage 7: two fresh MVP runs, one successful run per goal, real mixed-game transfers and all recovery/notification cases. |
| 27 | `codex/release-hardening` | Stage 7: compatibility, performance, migration, clean install/uninstall, independent review, docs and licence audit. |
| 28 | `codex/version-one-release` | Supported requested categories/goals, reproducible packages, checksums, tagged release and maintenance guide. Explicit release approval required. |

Start each branch from updated `main` after its prerequisites merge. If deliberate
stacking is necessary, name the dependency and target the appropriate base; do not
mix the new feature into an existing unrelated PR. Stash, reputation and skill
work have separate adapters but still use the same receipt/state authority.

If an increment becomes too large, split it by observable behaviour and update
this table. Every feature branch includes its own option tests and live acceptance;
the final matrix does not postpone basic validation until the end. No automatic
merges or public releases.

Transition shuffling, equipment licences beyond these rewards, traps/DeathLink
and xrRazom co-op remain separate exploratory branches after the supported scope.
They must not delay or silently replace the requested checks, rewards and goals.
