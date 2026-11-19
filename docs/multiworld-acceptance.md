# Step 28: expanded multiworld verification

Stack base: #31. The real-server harness generates and hosts two fresh MVP seeds
and one full-options seed for each of six goals. Each has two GAMMA slots plus
APQuest. It uses the pinned upstream generator, MultiServer, CommonClient and
actual loopback websocket traffic. Checks/items, cross-slot transfers, goal
packets, named notices, older acknowledgements and durable server restart are
verified against the server's actual saved state.

Game snapshots in this harness are synthetic and carry protocol 3's exact settings
digest, matching the updated add-on. These are eight additional server
cases, not eight in-game playthroughs. Engine callback, reward and goal adapters
have separate mocked Lua regressions; they are not mislabeled as live engine
evidence. Owen explicitly reserved engine verification for each PR after merge.
No game is launched by the harness or by the verifier.

Recovery checks all notification batches, not just the first 64 scouted checks.
A fresh companion reconnects to a restored server, recovers the same ordered
history and monotonic checks, then reconstructs the prior named notices through
bounded scouting polls. An older game receipt count cannot truncate server
history. Physical reward replay follows the documented older-save policy;
network history recovery alone does not prove crash-proof item creation.

## User acceptance after merge

For each feature PR, start from the isolated MO2 development profile, record its
source commit and seed/preset, then use that step's document for the actual engine
trigger. Close the game before deploying another source revision. Preserve the
entire appdata/profile backup procedure; never test with the normal multiplayer
installation. The remaining release matrix is:

| Run | Remaining engine evidence |
|---|---|
| MVP A / MVP B | Fresh Loner/Cordon saves, real check sends and actual rewards, save/load, offline checks and reconnect |
| Each alternate goal | Actual qualifying inventory, switch, dialogue or all five lab entries; actual completion packet |
| Mixed multiworld | Named incoming/outgoing/self notices, foreign item names and delayed PDA restoration |
| Recovery | Client/server restart, old-save rollback, pending reward failure, wrong-session refusal and bounded replay |
| Optional locks/travel | Every route, missing/hostile hubs, native restrictions and one-time travel consumption |

Record **passed / failed / not run** with logs and the exact source commit. Current
expanded engine rows are **not run**. The user's earlier pilot reload and third-map
acceptance remain recorded in the existing verification record; that acceptance
does not stand in for all expanded categories or a complete goal playthrough.

Automated result: the full verifier passes 581 covered tests and 16 untraced
cases: six 1,000-seed presets, two pilot server cases and eight expanded server
cases. All independent coverage gates pass. The full 257-check slots require
several 64-scout recovery polls; the harness explicitly drives every batch.
