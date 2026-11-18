# Archipelago Mod Configuration Menu

Enable `GAMMA Archipelago DEV` in the isolated development MO2 profile, restart
the game and open **Mod Configuration Menu → Archipelago**. The page is the
extension point for later Archipelago settings. Connection/IP controls are not
implemented in this increment; networking still belongs to the companion client.

The page always shows **Spawn basic tools at my feet**. Load a save with a living
character before using it. Each valid click creates one `itm_basickit` world
object at the player's X/Z position and 0.2 metres above the ground origin so it
can settle without clipping.
The spawn call omits an owner/parent ID. It does not insert the toolkit into the
inventory; pick it up from the ground. The action sends a success/failure PDA tip.

This is an explicit development action. It does not require an AP connection or
alter checks, completion, item history or saved receipt counters. Menu discovery
and opening do not create items. The callback refuses to create items in the main
menu or when the character is dead/unavailable. It rechecks those conditions and
the isolated appdata root when clicked, including direct calls after a stale menu.

## Integration

`gamma_ap_mcm.script` supplies the normal MCM `on_mcm_load` options tree, with the
stable root ID `gamma_archipelago`. Its button uses the installed MCM's `functor`
interface, with availability checked inside the action rather than a visibility
condition. `gamma_ap_actions.script` owns the engine operation.
English strings are in `gamedata/configs/text/eng/st_gamma_archipelago.xml`.
No MCM/base scripts are replaced. Future connection controls should use this
namespace and a defined client configuration contract rather than a second
network implementation inside Lua.

The implementation references the installed `ui_mcm.script` button/discovery code
and Anomaly's `alife_create` helper. This work is independent of the unmerged
callback-probe branch and does not require that diagnostic add-on.

## Verification

LuaJIT tests invoke the actual menu definition and button callback with engine
boundaries mocked. They check discovery has no spawn side effect, translated
control keys, exact section/coordinates and absence of an owner argument, one
item per click, stale-menu refusal, wrong roots, missing item definitions and
creation failure. Packaging tests require all seven scripts and the strings XML.

On 18 November 2026, the isolated GAMMA 0.9.5 game was launched through the
`Archipelago DEV` MO2 profile with `-ltx user_ap_dev.ltx`. Opening **Mod
Configuration Menu → Archipelago** from the main menu visibly displayed **Spawn
basic tools at my feet** and the instruction to load a living character first.
Main-menu visibility passed in the actual engine.

Remaining live acceptance: load a fresh development save, click once, observe a
single toolkit on the ground, pick it up and save/load. Check that AP receipts
and checks remain unchanged. Automated engine mocks do not establish these
in-game outcomes.

On the development machine, the eight add-on files have been copied to
`D:/GAMMAAP/mods/GAMMA Archipelago DEV` and enabled only in `Archipelago DEV`.
Their contents match the source and they are not hardlinks. The installer's
default profile remains unchanged. Development appdata, profile and MO2 settings
were backed up outside Git before deployment. The game was closed during setup;
the ground pickup still requires live verification.

## Missing-button regression

The first version used the spawn-availability check as an MCM visibility condition.
The engine log showed its filesystem root retaining `d:/anomalyap/bin/..`, while
the guard required the spelling without `bin/..`. This rejected the development
installation and hid the button; the same comparison also blocked the AP bridge.

The menu now keeps the button visible and validates only when clicked. A shared
`gamma_ap_paths` module canonicalizes the absolute engine path, including `.` and
`..`, before comparing it to the same fixed development root. It still rejects
the original game, other roots, traversal above the drive root and ambiguous
Windows path components. Regressions reproduce the original rejection and check
both the menu action and bridge with the engine's `bin/..` spelling.
