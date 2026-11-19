# GAMMA compatibility investigation — 19 November 2026

## Scope and evidence

Read-only inspection of the saved `Archipelago DEV` profile, installed loose
sources and the existing development log. No game was launched, no settings or
third-party files were changed, and no new native result is claimed. This source
audit is independent of the PDA localization PR. The normal game was untouched.

The selected MO2 game root and every executable/working directory point into the
development installation. The saved profile has 606 enabled entries and no missing
enabled mod directories. Candidate order includes overwrite first, then enabled
mods in saved priority order, then loose game files. Archives, runtime patches,
unsaved MO2 edits and the live engine winner remain unresolved.

The latest available development log was last written at **2026-11-19 00:35:48
UTC**, after starting at 00:31:27. It reports Anomaly 1.5.3, core 9959, Modded Exes
MT-TEST 2026.05.15. None of the four historical error signatures appears in that
log. It includes the Extra Level Transitions MCM load and an orderly shutdown.
Absence from this session does not establish that unused scripts compile or that
their dependent features work. Earlier recorded errors remain historical evidence.

## Findings

| Consumer | Current source finding | Interpretation and next action |
|---|---|---|
| `a_faction_prices.script`, GAMMA UI | Line 16 accesses `faction_stocks.get_trader_community`; no enabled loose provider or extracted baseline script was found. LuaJIT compilation itself passes. | Potential obsolete/lazy-loaded integration. Trace the intended caller and archive provider before changing it. AP reputation uses `relation_registry` personal goodwill, not this pricing script. A missing pricing helper does not by itself prove AP goodwill fails. |
| `mags_patches.script`, UDP-9 Carbine | Lines 4 onward access `magazine_binder`. Provider copies exist in installed magazine mods, but those mods are disabled in the DEV profile. Compilation passes. | An enabled optional compatibility consumer with disabled providers. Do not enable magazine systems merely to silence this: they conflict with the ordinary unjam/reload setup. Determine whether the patch should be conditionally loaded or removed by the supported upstream configuration. |
| `zz_ui_inventory_better_stats_bars.script`, GAMMA Keybinds fixes | Line 41 accesses `better_stats_bars_mcm.op` while initializing defaults. The provider is installed in Better Stats Bar, which is disabled. Compilation passes. | Another optional-provider mismatch. The DEV profile enables Momopate's Detailed Weapon Stats. Do not enable an alternate stats UI without reviewing that combination. This is an inventory-stats override, not proof of a PDA-key handler failure. |
| `zzz_mspizza_Godis_ZoomCalc.script`, 3DSS for GAMMA | The installed source fails LuaJIT 2.1 `loadstring` compilation at line 113: unexpected symbol near `/`. Lines 113/124 use C-style comment delimiters. | Confirmed static syntax defect. A minimal source-level repair would replace those delimiters with Lua long-comment delimiters, but only as a version/hash-bound upstream or separately owned compatibility patch after checking licensing and the intended script role. No vendor file was edited or packaged. |

The extracted base scripts also contain no references to the three missing provider
names. That search does not inspect every installed archive or engine-defined
global. Do not describe missing loose candidates as proven runtime-global absence.

### Extra transitions and PDA keys

Extra Level Transitions and its facing-fix mod are enabled. The saved loose
candidate for `lc_extra_transitions.script` compiles under LuaJIT, and its MCM
provider is enabled. The latest log contains its MCM load without a corresponding
error. The AP add-on does not replace this script. Markers, transition triggers
and compatibility with zone locks still need the user's in-game acceptance.

The PDA action `active_jobs` has different bindings in the two development configs:
`user.ltx` uses Caps Lock (`kCAPITAL`); the custom AP DEV DX11 entry selects
`user_ap_dev.ltx`, which uses P (`kP`). Ordinary MO2 entries do not pass that custom
configuration argument. This explains a configuration-dependent expected key;
it does not prove the key works in an untested session. The winning loose
`actor_effects.script` candidate is GAMMA 3D PDA and Headlamp Animations. Its source
compiles. Launch through the isolated MO2 entry so its virtual files are present.

## Repeating the source inspection

From a source checkout, run:

```powershell
& 'D:/GAMMAAPTools/python-env/Scripts/python.exe' tools/inspect_probe_sources.py
```

The watched list now includes all four consumers, the three provider scripts and
the transition MCM provider. The JSON reports candidate owners/hashes and explicitly
leaves the runtime winner unverified. Save this private installation inventory
outside Git. The inspector does not execute installed code or change files.

For syntax investigation, compile the selected source with LuaJIT 2.1 `loadstring`
without calling the returned function. This detects the zoom-script syntax error;
it cannot establish engine globals, callback registration or behavioral safety.
All six inspected consumer/transition/PDA sources compiled except the zoom script.
The failing zoom source SHA-256 is
`6ddb41a326b4545d33f4a935c3bab628e452f499317f27a9c95feff804dd9c49`.
Retain the full local report outside Git when comparing a subsequent update.
Replacing only the two standalone comment delimiters in an in-memory copy made
that copy compile successfully. It was not executed or written back to the game;
syntax success alone does not verify zoom behavior.

## Follow-up and native acceptance

1. Keep the installed baseline unchanged until the user's comparison test. Capture
   a fresh MO2-launched DEV session with AP disabled, then enabled; compare these
   four errors and the feature actually affected. Keep logs private.
2. Confirm transition markers/triggers and the PDA key using the exact same MO2
   entry/configuration. Record the entry and config, not private save names.
3. For an error reproduced in the baseline, check the supported GAMMA update or
   optional-mod configuration first. Capture exact hashes before a narrow vendor
   compatibility repair. Preserve the current source and backup/restore path.
4. Exercise AP goodwill/trader tiers, gear/weapon classes and zone-key transitions
   separately. Passing syntax or missing old log errors is not their acceptance.

Status: source investigation **passed**; static zoom compilation **failed**;
third-party remediation **not implemented**; new native verification **not run**.
No dependency baseline was updated. Save formats, published IDs, reward/check
logic, installed developer panel and deployed bundle are unchanged.

Full local verification **passed** with a separate tooling runtime: 720 covered
Python/Lua tests, 32 untraced generator/server tests and five Node tests, **757
total**, including the 6,000-preset seed matrix. Each owned Python runtime module
measured 100% lines/branches; Lua executable-line gates passed. Lua branch coverage
is not measured. The new regression ensures the source inventory exposes enabled
consumers while omitting providers in disabled mods. This branch shares only the
small Windows HTTP test-fixture prerequisite with the separate PDA PR. Windows
and Linux CI for the final head are an additional delivery gate.
