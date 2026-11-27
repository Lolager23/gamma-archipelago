# Manual repair of the existing Owen/Mini goodwill conversion

The corrected add-on must be installed before these functions exist. These are
Lua statements for GAMMA's debug **Execute String** field, not AP chat commands.
The active GAMMA debug launcher provides `NPC Logic / Execute` (key 0 in
its editor list), opening a Lua Execute dialog. The pinned Anomaly UI also
has an Execute String field and Execute button in its Advanced tab. Both callbacks
run the entered Lua. The debug command console also supports
`execute <Lua statement>`. Engine tilde-console aliases are not assumed here.
GAMMA UI layout/hotkeys and the native result still need player verification.

## Preparation

1. Make a separate manual save before repair, then close the game and companion.
2. Back up the complete Anomaly appdata tree, MO2 profiles/overwrite/configuration
   and the current mod. Owen's target is only AnomalyAP/GAMMAAP; Mini uses their
   existing enrolled AP installation. Keep the server's current seed and progress.
3. Install the corrected MO2 package by merging into the existing AP mod. Preserve
   private developer-panel files. Load that same character through MO2.
4. Open GAMMA's debug menu and select `NPC Logic / Execute` (or the older
   Advanced / Execute String field if using that UI). First run:

```lua
gamma_ap_game.goodwill_report()
```

The report prints Mercenary (`killer`), Military (`army`) and Bandit personal
standing alongside each dedicated AP floor. Output also appears in PDA news and
the game log. The floor is derived from the named rewards actually applied in this
save, not from server items still pending. Allies are never reset by this repair.

## Recommended practical repair when original natural standings are unknown

```lua
gamma_ap_game.repair_goodwill_ap_only("CONFIRM_AP_ONLY")
```

This explicitly discards unknown natural goodwill for those three factions and
sets each to its dedicated AP-earned floor. It retains all named AP rewards and
stops converted Loner rewards from benefiting the three hostile factions again.
It leaves Free Stalkers, Clear Sky, Duty, Freedom and Ecologists untouched. The
normal faction-to-faction hostility table and individual NPC grudges are unchanged.
It is a clean AP-only baseline, **not** an exact rollback of the previous migration.

Close the debug menu and resume unpaused gameplay. The saved plan waits for a ready
world frame before changing native standings. Reopen the field and run:

```lua
gamma_ap_game.goodwill_report()
```

Wait for `Repair completed; shared rewards limited to allies`, then make a new
manual save. Reload and check the report again. Repeating the repair command is
refused once a plan exists; polling/reloading a partial plan uses the same absolute
targets. A native setter failure can retry. If an unprocessed faction's standing
changed independently after planning, the repair refuses to overwrite it: load
the pre-command save and prepare the correction again.

## If the correct personal standings are known

Use explicit desired personal goodwill in this fixed order: Mercenaries, Military,
Bandits. Every target must preserve any dedicated AP-earned floor. With no dedicated
receipt there is no AP floor, so a known negative personal standing is valid.
For example, **only if 600/800/500 are the correct desired personal standings**:

```lua
gamma_ap_game.repair_goodwill(600, 800, 500, "CONFIRM")
```

The first report supplies the applicable minimums. Do not set all three to zero or
subtract `Loner count * 250`: capped grants, old AP floors and natural changes make
that arithmetic unreliable. Setting native values without the mod correction also
fails because the old shared floor can raise them again.

## Exact historical restoration

If exact natural standings matter, the dependable source is a matching pre-update
GAMMA save, loaded with the corrected add-on and a version-2 allied migration request
before entering the world. That restores the native game to the earlier save point;
subsequent native quest/inventory progress is lost. Keep the AP server seed/save:
checks remain complete and the companion replays the server's ordered history
relative to that restored save. Do not edit server receipt IDs or regenerate the seed.

The shared reward definition in a seed's existing server archive is unchanged. The
Owen/Mini run uses legacy faction-specific placements and already has dedicated
hostile rewards, so its receipt IDs and configuration remain valid. Existing mode-1
all-eight seeds keep their published logic and are not eligible for this legacy-run
repair. New generations use allied mode 2 with the dedicated hostile quotas restored.

Validation uses mocked engine boundaries and real AP generation/server tests. No
agent runs these statements in a live game. Backups and in-game acceptance are the
players' responsibility. Repair/native mutation and saving are not transactional.
