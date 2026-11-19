# Foundation verification record

## Baselines

Recorded 18 November 2026. Anomaly 1.5.3 reached its vanilla main menu in
`D:/AnomalyAP`. GAMMA launcher v8.6 was started from `D:/GAMMAAP` and the user
started the official installation. Download and full GAMMA launch remain pending.
The new MO2 configuration points to the development Anomaly directory.

After foundation development, the protected installation's 163,937-file baseline
has zero added, missing or size/timestamp-changed files and zero filesystem links.
All 859 backed-up appdata/profile files still match their original SHA-256, and
the backup copies also match. Detailed private inventories remain outside Git.

Archipelago reference: tag 0.6.8, commit
`54803be064fc7e80c4628777ed0b46a9390f255f`. Local Python: 3.12.3 on Windows.

The initial published documentation bootstrap `e467777` inherited the machine's
work author/committer email despite the local personal user setting. Local
`author` and `committer` overrides now explicitly use the requested personal
address, with commit/push checks. Global work settings and published history are
preserved. The private remote belongs to personal account `Lolager23`.

## Automated evidence

`tools/verify.py` passes locally with 91 regression/integration tests under coverage
and two additional real-server tests. The world generation regression checks
1,000 seeds. Every owned Python runtime module currently has 100% line and branch
coverage. The three non-generated Lua modules reach 100% executable-line coverage;
Lua branch coverage is not measured. These numbers describe this finite pilot,
not the finished randomiser's correctness or game compatibility.

The real server tests generate an actual seed, host upstream MultiServer on a
loopback websocket, authenticate the real CommonClient, send all checks, receive
items, report the goal and reconnect. Both solo and mixed APQuest sessions pass.
Game snapshots in these tests are synthetic; the Anomaly engine is not running.

Packages are rebuilt twice and compared byte-for-byte. The `.apworld` is loaded
in a separate process through upstream's archive loader, without a loose copy
of the GAMMA world. Generated catalogues and MO2 package contents are checked.

Regressions cover canonical protocol parsing, malformed/partial data, unknown IDs,
duplicate and conflicting histories, wrong seed, old-save rollback, failed item
creation, bounded polling, save/load callbacks, path escapes, hardlinks, symlinks
and junctions. Real-server testing found and fixed use of the optional seed filter
instead of `server_seed_name`. A separate reconnect regression prevents empty
connection state from truncating the previously accepted item history.

Upstream warns that its optional `_speedups` extension is absent; the supported
pure Python fallback is used. Real-server tests run without coverage tracing due
to the local Python/C-backed YAML interaction described in the development guide.

## Remaining acceptance

The callback-probe increment has its own [source findings and evidence matrix](callback-probes.md).
Its local verifier passes 140 covered tests plus two real-server tests, with 100%
Python line/branch coverage and 100% executable-line coverage for the five owned
Lua modules. This remains automated evidence; no callback-probe in-game acceptance
has been marked passed.

- The Windows/Linux workflow is active at `.github/workflows/verify.yml` after
  the user authorised the required GitHub `workflow` scope. Hosted run evidence
  is linked from [PR #1](https://github.com/Lolager23/gamma-archipelago/pull/1/checks);
  inspect the current head's results separately from the local results above.
- Official GAMMA installation completion and final resolved-path audit.
- Development MO2 profile, copied add-on deployment and profile save/settings check.
- All engine checks listed in the development guide, including actual delivery.
- Measured crash/rollback recovery policy before MVP.

The first PR remains draft until its in-game acceptance is complete. No normal
multiplayer saves are used, and no claim of multiplayer compatibility is made.
