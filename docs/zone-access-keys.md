# Step 20: zone access keys

Stack base: #23. `rewards_zone_keys` adds one required permanent key for each of
32 non-start maps, IDs 28051701–28051732. Cordon is always open. Map checks are
required for an initial reachable exploration route; undersized required pools
are rejected. Keys cannot be placed behind their own destination entrance.

All entrances to a keyed region require its key, including alternate graph edges.
Global activities conservatively require access to every zone instead of claiming
all species, artefacts and story events occur in Cordon. Equipment-dependent
checks also require selected AP gear permissions. Radar/X19/X16 access accounts
for protection via a reachable Yantar supplier or the local orange stash claim.
This is conservative logical availability, not an ALife spawn-rate guarantee.

Runtime wraps native `ChangeLevel` and the engine's authoritative
`CALifeUpdateManager__on_before_change_level` packet hook, preserving delegates.
The inspected pinned engine calls the latter before save/cleanup for change-level
packets, covering native, extra and scripted routes using that engine path. Online
changers are examined in batches of at most 128 storage entries and disabled for
locked destinations. Only AP-owned disables are restored on unlock; previously
native-disabled changers stay disabled. Ownership is saved, without engine objects.
Unknown destinations are refused while keys are enabled. A fresh Cordon start is
required; another starting map refuses the configured seed.

The native packet callback returns void, so it cannot cancel a transition that
has already passed its dialog. Its fallback rewrites that packet to the actor's
current zone/position before native processing. This may cause a same-zone reload;
normal disabled changers and guarded script calls avoid that path. A third-party
engine that bypasses the inspected transition path is outside this contract.
Native quest/protection restrictions still apply; keys never turn devices off.
Before uninstalling from a keyed save, restore AP-owned disabled changers using
all keys and allow the bounded poll to finish. A clean non-AP save is preferred.

Full verifier: 480 covered tests plus two real-server cases; independent coverage
gates pass, including 100% Python access-rule and Lua zone-adapter coverage.
Tests cover all entrance rules, solver fill, key-dependent activities, unknown
routes, return paths, packet rewriting, wrapper composition, wrong starts and
native-disabled ownership. Lua branch coverage is not measured. Engine traversal
and transition-mod acceptance are not run, reserved for Owen after merge.
No game launch, deployment or protected-root changes occurred.
