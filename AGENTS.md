# Working rules

Read `docs/coding-standard.md`, `docs/git-workflow.md`, and the architecture before
changing code. Use the branch roadmap to keep each PR focused.

## Ownership and isolation

- `D:/Anomaly` and `D:/GAMMA` are the protected multiplayer installations. Never
  write there, run their installers, change their profiles, or load their saves.
- The development installations are `D:/AnomalyAP` and `D:/GAMMAAP`. Reject any
  deployment, bridge, installer or launcher path outside these explicit roots.
- Runtime state belongs under the development game's `appdata/archipelago`.
- Keep the source repository separate from the game. Deploy copies, never links.
- Never commit installation manifests containing private save names, credentials,
  access tokens, downloaded game files, or game saves.

## Implementation

- Use one explicit session coordinator and one authoritative state owner per
  process. No service locator, event bus, distributed services or hidden registries.
- Anomaly's required callback registration is the game adapter, not permission to
  scatter business rules across callbacks.
- Write regression tests for every corrected defect. Exercise failure paths,
  reconnect, duplicate delivery, wrong seed/slot and save rollback.
- Run the documented verification command before pushing. A coverage threshold
  is a minimum, not a substitute for meaningful assertions.
- Distinguish simulated tests, live local-server tests and in-game verification.
  Never mark the last category passed from mocks alone.

## Git

- Repository identity: Owen Welch <owenwelch@hotmail.co.uk>. Do not change global
  Git identity or borrow a work identity.
- Use `codex/` branches, conventional commit subjects and small coherent commits.
- Open draft PRs for work with unfinished acceptance checks; do not merge without
  the user's instruction. Do not bypass failing checks.
- Do not delegate to other agents unless the user explicitly requests it.
