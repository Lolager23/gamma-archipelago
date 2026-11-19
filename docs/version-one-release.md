# Step 30: v1 candidate and maintenance handoff

Stack base: [hardening PR #33](https://github.com/Lolager23/gamma-archipelago/pull/33).
This branch prepares a private 1.0.0rc1 candidate. It does not publish/tag v1,
merge the stack or mark deferred engine acceptance passed.

## Candidate contents

`python tools/prepare_release.py` requires clean committed source, rebuilds the
four deterministic packages and writes `dist/gamma-archipelago-1.0.0rc1.zip`
plus its `.zip.sha256` checksum. The candidate includes the APWorld, MO2 add-on,
separate probes, companion, guides, presets and `SHA256SUMS`.
Its `release-manifest.json` identifies the exact Git commit, pinned AP commit
and SHA-256/size of every payload. Metadata records unaccepted engine status,
no publication approval and the outstanding owner licence decision. Rebuilding
the same clean commit produces the same candidate without injected timestamps.
The preparer performs only local file operations and Git reads.

## Acceptance before v1

| Gate | Current state |
|---|---|
| Thirty implementation increments with reviewable PRs | Implemented; see the PR index |
| Local verifier, coverage, real AP loading/server and seed matrix | Passed at PR #34 review: 674 tests; see verification record |
| Windows and Linux CI | Check current PR head, not an older green revision |
| Per-merge engine checks, two MVP playthroughs and every alternate goal | Not run for expanded scope |
| Engine performance and mod interactions | Not run |
| Independent human review | Not run |
| Owner's public licence decision | Pending |
| Publication approval, v1 tag and GitHub release | Not requested or performed |

The implementation and candidate are concrete while these acceptance rows stay
open. Transport simulations are not playthroughs. Use a fresh Loner/Cordon
character for acceptance. The installed baseline is the isolated Anomaly 1.5.3 /
GAMMA installation from 18 November 2026; another engine/mod baseline needs its
own recorded acceptance. Python 3.12 and AP 0.6.8 are the tested tooling versions.

## Maintenance

1. Merge/retest in order. Record commit, seed/preset, native versions and evidence
   for each actual result in the verification record.
2. Fix defects on focused `codex/<fix>` branches with reproducing regressions.
   Preserve published history and IDs.
3. Close game/client/server before updating. Back up the complete appdata,
   profile and configuration trees; never mix normal and development saves.
4. Keep world/client/add-on/source together. Upgrade through compatibility tests;
   rollback by restoring the matching older bundle and save.
5. Edit the authoritative catalogue and regenerate copies. New game/mod/API
   baselines require deliberate source inspection and acceptance.
6. After open gates close, prepare a clean candidate and verify its checksums.
   Tagging/publication remain a separate approved action.

White stashes use the finite Cordon roster. Zone keys are local exploration-chain
rewards; other rewards use normal multiworld placement. ALife encounter/task
availability requires playtests. Consumables can replay after older-save rollback;
no engine-level exactly-once claim is made. Co-op and exploratory stretch goals
are outside this candidate's supported scope.
