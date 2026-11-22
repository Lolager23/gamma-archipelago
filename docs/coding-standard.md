# Coding standard

## Purpose

Code must make its behaviour and ownership apparent to the next person reading
it. Prefer a direct function call and a small data structure over a framework.
Fix the underlying problem and leave an explanation where a decision is not
obvious. Do not introduce machinery merely because another project uses it.

## Structure and responsibilities

Keep Python under `src/gamma_archipelago`, the AP world under `apworld/gamma`,
the deployable Lua add-on under `mod/gamedata/scripts`, and tests under `tests`.
Use `tools` for build, verification and deployment commands. Game-generated files
belong outside the source tree. Test paths should mirror the code they exercise.

Keep the optional diagnostic add-on in `probes/gamedata/scripts`, packaged separately
from `mod`. Diagnostics must not send AP checks or automatically grant rewards.

Use lower_snake_case for files, functions and variables, PascalCase for Python
types and UPPER_SNAKE_CASE for constants. Keep Archipelago's required framework
names where an extension point dictates them. Prefix game scripts `gamma_ap_`.

Each module owns one coherent responsibility. Aim for functions below 40 lines
and implementation modules below 250 lines. Exceed those guides only with a clear
reason in the PR; split by responsibility, not arbitrary line count. Avoid
miscellaneous `utils`, `helpers`, `manager` and `common` dumping grounds.

There is one Python session coordinator. It coordinates transport, the file
bridge and validation through explicit dependencies; it does not implement all
three. Lua game callbacks delegate to a small session state module. There are no
god objects, message buses, microservices, distributed databases, global mutable
registries or automatic dependency discovery in our code. The engine's required
callback mechanism remains confined to the adapter.

## Clarity and correctness

- Python targets 3.12 and uses type annotations on public functions and data.
- Lua targets Anomaly's LuaJIT/Lua 5.1 behaviour. Do not rely on Lua 5.4 features.
- Prefer immutable values and pure transformations for protocol and game rules.
- Name quantities with units: `poll_interval_seconds`, `received_item_index`.
- Reject invalid input at boundaries. IDs, sequence numbers, protocol versions,
  seed identity and slot identity must be checked before state changes.
- Catch specific exceptions. Report actionable errors; do not silently continue
  after a failed write or reward delivery. Never use blanket `except: pass`.
- Use bounded input sizes, fixed filenames and atomic snapshot replacement.
  Treat messages as data. Never `eval`, `exec` or load executable Lua from the bridge.
- Do not block the game update loop with network operations. Poll files at a
  bounded interval. Network work belongs to the companion client.
- Comments explain why and document limits. Names and short functions explain how.
- Logs identify the operation and relevant state, without passwords, tokens or
  personal save filenames. Keep debug output bounded.

## Tests and coverage

Every behaviour change includes meaningful unit tests. Every bug fix adds a
regression that reproduces the original failure before it passes with the fix.
Use deterministic inputs and explicit clocks; avoid sleeps and live internet in
unit tests. Mock the external boundary, not the function under test.

The required gate is **at least 95% line coverage and 95% branch coverage** for
changed owned Python production modules on normal PRs, and every owned module on
full releases. Protocol validation, session identity and receipt
ordering must reach 100% of both. Owned Lua must meet the same 95% line/branch
target when the runtime coverage collector can measure it; never claim a branch
metric the collector cannot measure. Until Lua branch instrumentation is available,
require 95% executable-line coverage and explicit tests for both outcomes of every
decision, with that limitation recorded in the PR. Do not add exclusions to make
a failing number pass. Generated catalogue tables may be excluded from executable
coverage only when separately checked against their source catalogue.

Tests must cover:

- Initial connection, refusal, disconnect, retry and resynchronisation.
- Offline checks retained until the server acknowledges them.
- Duplicate packets, overlapping item batches, index gaps and out-of-order input.
- Seed/slot mismatch, unsupported schema and malformed or incomplete files.
- Save/load and older-save rollback. Permanent unlocks and consumables have
  different recovery needs; do not pretend both are solved by one saved counter.
- Reward creation failure and crash boundaries between creation and saving.
- Forbidden paths, links into the normal installation and wrong launch targets.
- A generated single-player seed and a mixed-game multiworld with actual server
  traffic, then the same checks inside GAMMA.

Normal verification selects the affected component's unit/regression tests and
coverage gates; keep adding the same meaningful tests and regressions. The complete
suite, exhaustive seed sweeps and all-module coverage run for full releases.
See [Testing policy](testing-policy.md) for commands, component boundaries and CI.
Live-server and in-game smoke tests produce separate evidence.
A green unit suite is not a declaration that a game build works.

## Review and maintenance

PRs explain the trigger, observable result, validation and known limitations.
Remove dead code and abandoned settings. Update documentation and compatibility
records when behaviour changes. Pin tool and dependency versions; update them in
a dedicated compatibility PR. Prefer standard libraries and upstream Archipelago
extension points to copied implementations.
