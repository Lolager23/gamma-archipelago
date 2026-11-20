# Step 20: zone access keys

Stack base: #23. `rewards_zone_keys` adds one required permanent key for each of
32 non-start maps, IDs 28051701–28051732. Cordon is always open. Map checks are
required for an initial reachable exploration route; undersized required pools
are rejected. Keys cannot be placed behind their own destination entrance.

The fill reserves a local exploration chain: each next key comes from a map
already reached, and its destination is adjacent to the unlocked frontier.
Yantar precedes psi-gated maps. Zone keys remain local to their GAMMA slot;
other rewards use ordinary multiworld fill. This prevents circular placement
in map-only seeds, including regression seeds 1, 4, 5 and 22.

All entrances to a keyed region require its key, including alternate graph edges.
Global activities conservatively require access to every zone instead of claiming
all species, artefacts and story events occur in Cordon. Equipment-dependent
checks also require selected AP gear permissions. Radar/X19/X16 access accounts
for protection via a reachable Yantar supplier or the local orange stash claim.
This is conservative logical availability, not an ALife spawn-rate guarantee.

Runtime wraps native `ChangeLevel`, its delayed `change_level_now` helper and the
engine's authoritative
`CALifeUpdateManager__on_before_change_level` packet hook, preserving delegates.
The inspected pinned engine calls the latter before save/cleanup for change-level
packets, covering native, extra and scripted routes using that engine path. Online
changers are identified by exported `clsid.level_changer`/`level_changer_s` values
(the baseline provides `isLc`, not `IsLevelChanger`), examined in batches of at
most 128 storage entries and disabled for locked destinations. Only AP-owned
disables are restored on unlock; previously
native-disabled changers stay disabled. Ownership is saved, without engine objects.
Unknown destinations are refused while keys are enabled. A fresh Cordon start is
required; another starting map refuses the configured seed.

The native binder is guarded after successful spawn when a loaded AP session is
available; the periodic scan reconciles later permission changes. Before save
restoration, no ownership changes are made against transient startup permissions.
Extra Level Transitions' `teleport_actor` is guarded before its time advance,
travel flag, effects and delayed call, preserving its delegate for allowed trips.

The native packet callback returns void, so it cannot cancel a transition that
has already passed its dialog. Native silent changers also ignore the enabled
flag. The previous fallback reused the actor's current position inside the
trigger, causing repeated same-zone autosaves/reloads in Owen's locked-Agroprom
test on 20 November 2026. The corrected fallback searches the finite game graph
for the nearest source-level point at least 30 metres away, outside every online
native transition volume with a 10-metre margin and the configured extra-transition
radii plus 10 metres. It writes that point's matching game/level vertices and
retains heading. Recovery does not rely on a previously cached position, so an
existing save in a trigger can recover too. One same-zone reload can still occur;
the character may be moved some distance within the source map. This verifies
trigger clearance, not freedom from NPCs or environmental hazards. If no qualifying
point exists, the hook raises an actionable error requesting an earlier save,
instead of forwarding the locked destination or repeatedly reloading the trigger.
Normal disabled changers and guarded script calls avoid this late path. A third-party
engine that bypasses the inspected transition path is outside this contract.
Native quest/protection restrictions still apply; keys never turn devices off.
Before uninstalling from a keyed save, restore AP-owned disabled changers using
all keys and allow the bounded poll to finish. A clean non-AP save is preferred.

Original Step 20 verifier: 480 covered tests plus two real-server cases; independent coverage
gates pass, including 100% Python access-rule and Lua zone-adapter coverage.
Tests cover all entrance rules, solver fill, key-dependent activities, unknown
routes, return paths, packet rewriting, wrapper composition, wrong starts and
native-disabled ownership. Lua branch coverage is not measured. Engine traversal
and transition-mod acceptance are not run, reserved for Owen after merge.
See the verification record for loading-loop regression and deployment evidence.
