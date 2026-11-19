# Agent instructions

These instructions apply throughout this repository. They turn the project docs
into working rules for implementation, review and verification. Keep this file
and the referenced docs consistent when an agreed decision changes.

## Read before working

Start with `git status --short` and preserve existing user changes. Read the coding
standard, Git workflow and architecture before changing code. Use the remaining
documents for the part of the task they own:

| Document | Use it for |
|---|---|
| [Coding standard](docs/coding-standard.md) | Structure, clarity, regression tests and coverage |
| [Git workflow](docs/git-workflow.md) | Personal identity, commits, branches, reviews and releases |
| [Architecture](docs/architecture.md) | Component responsibilities and state ownership |
| [Execution plan](docs/execution-plan.md) | Stages, investigations and acceptance evidence |
| [Expanded checklist](docs/expansion-plan.md) | Requested category options, PDA messages, reward contracts and staged acceptance |
| [Branch roadmap](docs/branch-roadmap.md) | Increment boundaries and branch dependencies |
| [Randomisation plan](docs/randomisation-plan.md) | Candidate content, MVP and final product goals |
| [Development environment](docs/development-environment.md) | Backups, isolation, installation and restore |
| [Development guide](docs/development-guide.md) | Tooling commands, deployment and game acceptance |
| [Verification record](docs/verification-record.md) | Recorded results, limits and outstanding checks |
| [Resources](docs/resources.md) | Primary references and pinned upstream baselines |

Treat proposed content as a plan until it has implementation and evidence. The
three-region pilot is a transport proof; it is not the MVP or proof of multiplayer
compatibility. Keep later roadmap increments out of the current PR unless the
user changes its scope. Do not delegate to other agents unless explicitly asked.

## Protect the normal game

- `D:/Anomaly` and `D:/GAMMA` are protected multiplayer installations. Never write
  there, run their installers, alter their profiles or load their saves for tests.
- Game deployment, launch and installer targets are restricted to `D:/AnomalyAP`
  and `D:/GAMMAAP`. Validate resolved paths, working directories, appdata, profiles,
  mods, downloads and overwrite destinations before use. Reject crossover paths.
- Keep source separate from installed files. Deploy copies, never hardlinks,
  symlinks or junctions. Do not copy the multiplayer engine or patched gamedata.
- Runtime bridge files belong only in `D:/AnomalyAP/appdata/archipelago`. Tooling,
  the pinned upstream checkout and the separate AP runtime use `D:/GAMMAAPTools`.
  Do not modify the shared Archipelago installation or the upstream checkout.
- Before installation or changes affecting save storage, follow the documented
  full appdata/profile/configuration backup and SHA-256 verification procedure.
  Keep backups and private inventories outside Git under the documented D: paths.
- Wait for installer completion before add-on deployment. Use the `Archipelago
  DEV` profile with separate saves/settings and a fresh single-player test save.
  Verify an unmodified development baseline before enabling the add-on.
- Preserve existing shortcuts; development shortcuts must say `AP DEV`. Recheck
  protected-tree inventories and backups after environment changes. Restore the
  normal installation only when the user explicitly requests it.
- Never commit game assets, saves, credentials, private save names, installation
  manifests or downloaded archives. Source control does not replace save backups.

## Structure and implementation

| Path | Responsibility |
|---|---|
| `src/gamma_archipelago/` | Typed protocol, file bridge, paths and session core |
| `apworld/gamma/` | Upstream AP world definitions and CommonClient adapter |
| `mod/gamedata/scripts/` | Additive Lua game adapter, state and protocol modules |
| `probes/gamedata/scripts/` | Separate opt-in diagnostic callbacks; never bundle into the pilot |
| `tests/unit/`, `tests/lua/`, `tests/integration/` | Mirrored behaviour and integration tests |
| `tools/` | Build, verification, bootstrap, deployment and launch commands |
| `docs/` | Design, standards, plans and evidence |

- Use Python 3.12 with typed public interfaces and LuaJIT/Lua 5.1 compatible Lua.
  Use clear names, explicit dependencies, small functions and cohesive modules.
  Aim for functions under 40 lines and modules under 250; explain exceptions.
- Use one explicit session coordinator and one authoritative state owner per
  process. No god objects, service locators, event buses, distributed services,
  hidden registries or miscellaneous utility dumping grounds.
- The world owns generation rules; CommonClient owns upstream networking; the
  game adapter owns engine access. Keep callbacks thin and network operations out
  of the game update loop. Prefer additive callbacks over base-script edits.
- Keep `src/gamma_archipelago/catalog.json` authoritative. Regenerate the world
  catalogue and Lua table with `tools/build.py`; do not edit generated copies.
  Never recycle published IDs. Schema/ID changes need a migration or documented
  breaking version, with compatibility evidence.
- Validate protocol versions, seed/team/slot identity, IDs, sizes and receipt order
  before mutation. Use fixed filenames, bounded polling and data-only snapshots.
  Keep one writer per direction and atomic client snapshot replacement. Never
  evaluate bridge content as Python or Lua code.
- The server owns checks and ordered item history; the save owns applied receipts.
  Preserve monotonic checks, reject conflicting history and refuse wrong sessions.
  A file write is not an item acknowledgement. Treat permanent unlocks and
  consumables separately when designing recovery. Do not claim crash-proof
  exactly-once delivery across item creation and saving.
- Catch specific exceptions and report actionable, bounded errors. Avoid silent
  failures and sensitive logs. Comments explain decisions and practical limits.
- Check primary upstream references against the pinned source and active GAMMA
  overrides. Record engine probes; community examples alone do not prove support.
  Change dependency/game baselines through a deliberate compatibility increment.

## Verification and evidence

Add meaningful tests for behaviour changes and a reproducing regression for every
bug fix. Use deterministic inputs and explicit clocks; mock external boundaries.
Exercise disconnect/reconnect, offline checks, duplicate/overlapping/out-of-order
items, gaps, wrong seed/slot, malformed/partial files, save/load, older-save rollback,
reward failure and forbidden paths/links. Add generation and game-gate tests when
changing progression; never place an unlock behind its own requirement.

Run the documented verification command before pushing:

```powershell
& 'D:/GAMMAAPTools/python-env/Scripts/python.exe' tools/verify.py
```

For another environment, use its Python environment and explicit AP tooling paths:

```text
python tools/verify.py --ap-source <pinned-upstream-checkout> --ap-root <separate-runtime>
```

- Require at least 95% line and branch coverage per owned Python runtime module;
  protocol validation, session identity and receipt ordering require 100% of both.
- Require at least 95% Lua executable-line coverage and tests for decision
  outcomes. Do not claim Lua branch coverage until the collector measures it.
  Generated tables are checked for catalogue parity; do not add coverage exclusions
  or weaken gates to pass a failing change.
- Run the complete verifier: lint, format, typing, regression/coverage, Lua tests,
  catalogue parity, reproducible packaging, actual APWorld archive loading and
  real generator/server sessions. Both the covered and untraced server passes
  are required; see the guide for the local Python/YAML tracing limitation.
- Check Windows and Linux CI for the current PR head. Retain reports and package
  checksums. An older green commit is not evidence for a new change.
- Distinguish mocked engine tests, actual AP server traffic and in-game testing.
  Follow the guide's engine acceptance checklist using fresh development saves.
  Record versions, commands, results and unresolved limits. Use `not run`, `passed`,
  `failed` or `blocked`; do not infer a game result from coverage or server tests.

## Git and delivery

- Use **Owen Welch <owenwelch@hotmail.co.uk>** for repository-local `user`, `author`
  and `committer` settings. Verify both effective identities with `git var`; global
  work author/committer overrides can defeat a local user email alone.
- Keep `user.useConfigOnly=true` and local `core.hooksPath=.githooks`. Do not change
  global work identity, bypass hooks or rewrite published history to fix attribution.
  Follow the documented identity guard policy and inspect outgoing commits.
- Use `codex/<purpose>` branches, conventional `type(scope): description` subjects
  and coherent commits. Follow the roadmap's sequential increments; identify
  dependencies when a branch deliberately builds on an unmerged PR.
- Review the complete diff and staged files. Exclude runtime artifacts, local
  evidence and secrets. Keep documentation current when behaviour changes.
- PRs explain the concrete behaviour, validation, save compatibility, isolation
  and remaining acceptance. Open unfinished work as draft. Do not bypass failing
  checks, merge, publish a release or make the repository public without the
  user's instruction. Never manufacture approval or completion evidence.
- Report what changed, which checks actually ran and what remains unverified.
  For release acceptance, follow the randomisation plan and Git workflow, including
  independent review, supported versions, migration policy, licences and checksums.
