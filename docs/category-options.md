# Step 05: generation configuration contract

Stack base: recovery PR #8. APWorld now defines 38 typed option fields: fourteen
check categories, seven reward categories, nine equipment modes, four starting
quantity percentages, a no-weapons preset switch, goal choice and two finite
milestone lists. Defaults preserve the three-check pilot and ordinary loadout.

Settings are normalized into an immutable core configuration, exported in slot
data with a deterministic digest and validated again by the companion. Session
configuration cannot change during reconnect. Old seeds without configuration
metadata remain supported. Unknown names, invalid numeric types/ranges, empty
check selection, nonascending/unbounded milestone lists and inconsistent AP-locked
loadouts are refused. An AP-locked start requires its unlock reward category.

At this step, only the existing map pilot is enabled. Each subsequent adapter PR
extends explicit capability declarations. Selecting a category, goal or restricted
start before its adapter exists fails generation with a clear error; it cannot
silently produce a different seed. This is intentional support validation, not
an implementation claim for the remaining steps. Dynamic pool-size and access
rules are added with the corresponding content/reward branches.

The world and client use the current checkout's core code in their launch tools,
including isolated worktrees. Full verification passes 304 covered tests plus
two real AP server cases, with 100% measured owned Python line/branch and Lua
executable-line coverage. No Lua branch metric is claimed.

The user instructed on 19 November that live game acceptance will be performed
by them after each merge. Do not launch/load the game automatically. Continue
automated validation and keep live outcomes explicitly not run until reported.
