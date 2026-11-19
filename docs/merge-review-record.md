# Sequential PR review and merge record

On 19 November 2026, PRs #2–#35 were reviewed and merged individually into
`main`, in dependency order, under Owen's explicit merge instruction. PR #1 had
already merged. Each successor incorporated the reviewed main before its own
review and verification; no stacked feature was merged wholesale or force-pushed.
The final checklist/audit reconciliation is delivered through
[PR #36](https://github.com/Lolager23/gamma-archipelago/pull/36), using the same
local verification and current-head Windows/Linux CI gates. Its exact final head
and merge are recorded by GitHub and the local audit alongside the records below.

## Merge gates and evidence

Each reviewed head passed the complete local verifier: lint/format, typing,
regressions, per-module Python coverage, Lua executable-line gates, catalogue
parity, deterministic packaging, archive loading, generation and real AP server
tests present at that increment. Both covered and untraced passes were required.
Windows and Ubuntu CI were completed successfully before each merge. Exact
commit check-run identities were also verified; PRs #2–#25 received an additional
REST audit of their recorded reviewed heads. No failing check was bypassed.

The local audit, review notes and logs are retained outside Git at
`D:/GAMMAAPTools/merge-review`. The linked PRs retain their source changes and CI
evidence. Counts below are pytest cases at each reviewed head; a later matrix
case contains 1,000 seeds, and Node cases are recorded in the final validation
summary rather than this pytest column.

| PR | Reviewed head | Main merge | Local pytest passes |
|---|---|---|---|
| [#2](https://github.com/Lolager23/gamma-archipelago/pull/2) | `c1d9844` | `f984c3b` | 142 + 2 |
| [#3](https://github.com/Lolager23/gamma-archipelago/pull/3) | `69dbc8d` | `6768c48` | 184 + 2 |
| [#4](https://github.com/Lolager23/gamma-archipelago/pull/4) | `5849f65` | `94a6faa` | 184 + 2 |
| [#5](https://github.com/Lolager23/gamma-archipelago/pull/5) | `9d5a0fb` | `0e6ee8c` | 184 + 2 |
| [#6](https://github.com/Lolager23/gamma-archipelago/pull/6) | `43f07c5` | `6f06438` | 185 + 2 |
| [#7](https://github.com/Lolager23/gamma-archipelago/pull/7) | `e8bd0c5` | `d38ced6` | 251 + 2 |
| [#8](https://github.com/Lolager23/gamma-archipelago/pull/8) | `545eaa0` | `d3bd38b` | 267 + 2 |
| [#9](https://github.com/Lolager23/gamma-archipelago/pull/9) | `40dc36b` | `d3ec932` | 328 + 2 |
| [#10](https://github.com/Lolager23/gamma-archipelago/pull/10) | `370d11c` | `4369b42` | 383 + 2 |
| [#11](https://github.com/Lolager23/gamma-archipelago/pull/11) | `3b1327c` | `bbf84ef` | 388 + 2 |
| [#12](https://github.com/Lolager23/gamma-archipelago/pull/12) | `aecdf7e` | `2f5bdb3` | 401 + 2 |
| [#13](https://github.com/Lolager23/gamma-archipelago/pull/13) | `c448339` | `b8bb457` | 413 + 2 |
| [#14](https://github.com/Lolager23/gamma-archipelago/pull/14) | `417782e` | `e4685db` | 419 + 2 |
| [#15](https://github.com/Lolager23/gamma-archipelago/pull/15) | `c0fa818` | `bb1db6f` | 433 + 2 |
| [#16](https://github.com/Lolager23/gamma-archipelago/pull/16) | `eb520ca` | `8476117` | 443 + 2 |
| [#17](https://github.com/Lolager23/gamma-archipelago/pull/17) | `5831659` | `7817a20` | 454 + 2 |
| [#18](https://github.com/Lolager23/gamma-archipelago/pull/18) | `ec0845a` | `3f94f79` | 469 + 2 |
| [#19](https://github.com/Lolager23/gamma-archipelago/pull/19) | `92b40fc` | `558738f` | 470 + 2 |
| [#20](https://github.com/Lolager23/gamma-archipelago/pull/20) | `8ed0df8` | `630d8cf` | 477 + 2 |
| [#21](https://github.com/Lolager23/gamma-archipelago/pull/21) | `91baf8a` | `18df404` | 497 + 2 |
| [#22](https://github.com/Lolager23/gamma-archipelago/pull/22) | `f89d386` | `c06e8ae` | 507 + 2 |
| [#23](https://github.com/Lolager23/gamma-archipelago/pull/23) | `9d31382` | `d866e5b` | 519 + 2 |
| [#24](https://github.com/Lolager23/gamma-archipelago/pull/24) | `ec5c3e7` | `e7a533b` | 528 + 2 |
| [#25](https://github.com/Lolager23/gamma-archipelago/pull/25) | `dbc8b01` | `75536fa` | 545 + 2 |
| [#26](https://github.com/Lolager23/gamma-archipelago/pull/26) | `4020e5c` | `7b31b03` | 563 + 2 |
| [#27](https://github.com/Lolager23/gamma-archipelago/pull/27) | `4514221` | `5379f31` | 565 + 2 |
| [#28](https://github.com/Lolager23/gamma-archipelago/pull/28) | `2dd93a2` | `a34b58e` | 569 + 2 |
| [#29](https://github.com/Lolager23/gamma-archipelago/pull/29) | `d86abdc` | `38c2bc1` | 570 + 2 |
| [#30](https://github.com/Lolager23/gamma-archipelago/pull/30) | `5bec6c0` | `0e2a7ae` | 572 + 2 |
| [#31](https://github.com/Lolager23/gamma-archipelago/pull/31) | `4bc3aa7` | `b7c8ce5` | 581 + 8 |
| [#32](https://github.com/Lolager23/gamma-archipelago/pull/32) | `8f09ece` | `c04bbba` | 581 + 16 |
| [#33](https://github.com/Lolager23/gamma-archipelago/pull/33) | `68cbeb9` | `6f04973` | 653 + 16 |
| [#34](https://github.com/Lolager23/gamma-archipelago/pull/34) | `ec1f47e` | `9f6ae5b` | 658 + 16 |
| [#35](https://github.com/Lolager23/gamma-archipelago/pull/35) | `d99dafe` | `ddb9ee8` | 719 + 32 |

## Review fixes

- Checkout command-line tools now import their own source before unrelated
  editable packages. Identity hooks accept already published GitHub merge history
  while rejecting newly authored commits with the wrong personal identity.
- Isolation documentation now identifies the actual separate appdata/save root;
  it no longer promises an unsupported MO2 profile-local-save option.
- Foreign PDA transfer identities retain the full exact signed 53-bit AP range.
- Haruka retry plans preserve naturally earned XP, levels and stats, and validate
  the native schema again before retrying recalculation.
- Quest rules require earlier story-chain permissions. Actual failing map-only
  zone seeds now use the validated local exploration-chain placement.
- Native pickup guards reset reused flags before each dispatch, including
  psi-only locks, while preserving other mods' current vetoes.
- Travel rejects nonnumeric, fractional and invalid vertices before consuming
  eligibility or invoking the native level change.
- Configured outgoing snapshots carry the settings digest, preventing stale
  checks, receipts and victory from a reused seed identity with different options.
  Expanded real-server fixtures use the same bound format.
- Restricted starts wait for confirmed money reductions and preserve lower
  natural balances on retry. Reconnection clears client-owned notices before
  publishing settings/history, without overwriting game-owned acknowledgements.
- Foreign notice IDs also have save-validation/reload regressions at zero,
  ten billion and both signed 53-bit limits.

Additional hardening and web-app review findings are recorded in the final
verification entry and their PR changes. Every reproduced code defect received
a regression before the fix; previous regressions remained in each full run.

## Acceptance boundary

No GAMMA process was launched or loaded. Neither normal nor development game
roots, MO2 profiles, deployed add-ons or saves were changed by this merge pass.
The original checkout and running local app were preserved; their running code
does not automatically become the merged revision.

Mocked Lua APIs and synthetic game snapshots establish adapter behaviour under
the harness, not native game compatibility. Expanded engine playtests, actual
PDA rendering, progression enforcement, native reward effects, performance and
full goal playthroughs remain pending. Earlier user-accepted pilot reload and
third-map evidence remains valid on its original basis.

This is merged experimental source and a private unaccepted candidate. No public
release, tag or repository-visibility change was made. Independent human review,
licence choice and the release acceptance matrix remain separate gates.
