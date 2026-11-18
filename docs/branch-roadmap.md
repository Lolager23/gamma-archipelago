# Branch-by-branch work

Branches are sequential by default. Each includes tests and documentation for its
own behaviour. Branches 01–03 establish feasibility; do not call them the MVP.

| Order | Branch | Deliverable and acceptance |
|---|---|---|
| 00 | `main` bootstrap | Charter, standards, plans, identity and isolated-environment record |
| 01 | `codex/archipelago-integration` | Buildable pilot `.apworld`, CommonClient bridge, Lua entry point, finite pilot checks, deployment guard, automated tests and first PR |
| 02 | `codex/game-callback-probes` | Measured task/stash/artefact/level hooks, clean mod-enable/disable and inventory-delivery evidence |
| 03 | `codex/session-recovery` | Wrong-seed protection, offline checks, ordered receipts, crash/save-rollback policy and regression matrix |
| 04 | `codex/check-catalogue` | Stable IDs for curated finite checks; duplicate and cancellation rules |
| 05 | `codex/progression-items` | Toolkits/detectors/protection pool; replacement of normal acquisition paths |
| 06 | `codex/access-rules` | Matching world/game gates; no self-locks, alternate routes covered |
| 07 | `codex/mvp-goal` | One complete story goal and final completion packet verified in-game |
| 08 | `codex/multiworld-validation` | 1,000 seeds, actual mixed-game session, two full runs, meaningful failure evidence |
| 09 | `codex/status-and-recovery-ui` | Clear connection, waiting, delivery and recovery status; useful PDA/notification behaviour |
| 10 | `codex/mvp-release` | Clean package install, player guides, compatibility matrix and reproducible experimental release |
| 11 | `codex/expanded-checks` | Additional proven regions/check types, each option tested independently |
| 12 | `codex/equipment-unlocks-spike` | Investigate permanent equipment/workshop permissions; keep/drop decision |
| 13 | `codex/transition-randomiser-spike` | Investigate connected, returnable shuffled Zone transitions |
| 14 | `codex/traps-and-deathlink-spike` | Opt-in, bounded effects; verify death/load and NPC failure cases |
| 15 | `codex/xrrazom-spike` | Separate test installation; decide host authority, slots and reward ownership; multiplayer originals remain protected |
| 16 | `codex/expanded-goals` | Supported faction/start/goal options with fresh logic and playthrough tests |
| 17 | `codex/release-hardening` | Compatibility, performance, migration, clean-machine tests and independent review |
| 18 | `codex/version-one-release` | Final chosen-scope acceptance, tagged packages, checksums, licences and maintenance guide |

If an increment becomes too large, split it by observable behaviour and update this
table. A spike must not become an unreviewable implementation branch. Keep the
first PR open until its own stated acceptance is met; later work is not silently
folded into it. No automatic merges or public releases.
