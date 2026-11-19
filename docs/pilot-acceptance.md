# Step 01: pilot acceptance

Stack base: planning PR #4, including the tested MCM baseline from PR #3.

| Case | Result and evidence |
|---|---|
| Rostok/Garbage checks and two applied rewards | Passed: captured server/game evidence in the verification record |
| Third-map trigger | Accepted by the user based on the shared trigger code |
| Ordinary game reload | Passed by user confirmation |
| AP socket reconnect | Passed in actual solo and mixed-game server tests |
| AP server persistence/restart | Passed: save the real server state, restore into a new Context and websocket listener, reconnect the real client; three checks, three items, session identity and goal survive |
| In-game third reward and goal packet | Not independently captured; remains live acceptance work |
| Game older-save rollback/crash policy | Existing regression coverage; measured engine recovery remains Step 04 work |

The restart test uses synthetic game snapshots. It establishes real AP server and
client behaviour, not physical movement or item creation in the Anomaly engine.
No existing live bridge files, game saves or server state are changed by tests.
Full local verification passes 129 covered tests and two real-server cases;
owned Python line/branch and six non-generated Lua executable-line coverage are
100%. Lua branch coverage is not measured.
