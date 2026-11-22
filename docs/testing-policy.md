# Development and release verification

On 22 November 2026 Owen requested affected-area testing for normal work and the
complete suite only for GitHub releases. Keep adding meaningful unit tests and
reproducing regressions; this changes execution frequency, not the test inventory.

## Normal branches and PRs

```powershell
& 'D:/GAMMAAPTools/python-env/Scripts/python.exe' tools/verify.py --base origin/main
```

For a stacked PR use its parent branch or base commit. The comparison includes
committed, staged, unstaged and untracked source changes, including deletions.
`--plan` prints and records the selection without running it. Missing Git history
or an unknown executable input fails explicitly instead of silently skipping it.

The boundaries are deliberately component-sized: related regressions run together,
without rerunning unrelated game, client and interface tests for every small edit.
The explicit mapping lives in `tools/verification_scope.py`.

| Changed area | Normal verification |
|---|---|
| AP world | World/integration regressions; exclude the unrelated network/client suite |
| Python core | Unit regressions plus dependent world/client integration |
| Companion networking | Unit and client regressions, plus its real server boundary without tracing |
| Game scripts/assets/probes | Native Lua adapter regressions and their existing executable-line gates |
| Generator UI/web runtime | Web regressions and Node checks |
| Build/bootstrap | Tooling regressions, reproducible packages and actual archive loading |
| Verification/CI tooling | Tooling regressions, including selection, routing and coverage enforcement |
| Shared catalogue/dependencies | All consuming components, without exhaustive generation sweeps |
| Test-only change | The changed tests; the Lua fixture requires its small native suite together |
| Documentation | Static checks; no unrelated runtime suite |

Every run retains `artifacts/verification-scope.json` with the base, changed files,
selected areas/tests and coverage targets. New tests need a sensible owning path;
update the explicit tooling mapping when adding a new tool test file. Formatting
and lint remain cheap repository-wide checks. Core changes also run strict typing.

Changed owned Python runtime modules retain independent **95% line and branch**
coverage; protocol/session modules require **100%**. Missing changed-module reports
fail. Unchanged imported children do not become coverage gates for a scoped run;
the aggregate threshold is replaced by these explicit per-module gates. The full
release run still measures every owned module. Lua retains its complete 95%
executable-line gate and decision tests; branch coverage remains unmeasured.

Large generation sweeps are marked `generation` and run untraced only for releases.
This includes the 10,000-seed preset matrix, 1,000-pilot sweep and broad category-pair
sweep. Focused generation, deadlock, access-rule and placement regressions remain
in the normal world suite. No tests or seed counts are deleted or reduced.

## Full releases

```powershell
& 'D:/GAMMAAPTools/python-env/Scripts/python.exe' tools/verify.py --full
```

Full verification retains all static checks, typing, Python/Lua regressions and
coverage, catalogue parity, reproducible packaging, actual APWorld loading, the
complete generation matrix and both covered and untraced server passes. It does
not launch GAMMA; native acceptance remains Owen's responsibility.

GitHub runs affected verification on PRs and pushes to `main`, on Windows and
Linux. Feature pushes do not duplicate an open PR's two jobs. Publishing a GitHub
release runs full verification; the manual workflow's explicit `full` choice is
also available for release preparation before publishing. Neither choice publishes
anything. A failed release check must be resolved before treating that release as
validated. Historical full-suite evidence remains historical, not evidence for
later commits.
