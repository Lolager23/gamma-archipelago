# Tool use permissions and free kits

Fresh seeds also use `progressive_tool_receipts=1`: three identical Progressive
Tools rewards supply and permit Basic, then Advanced, then Expert. Named tier
rewards and their geographic placement rules below describe the retained
`progressive_tool_receipts=0` contract. See [equipment classes](equipment-classes.md).

New seeds use `content_progression=1` and `tool_use_permissions=1`. AP rewards
unlock use of the six supported GAMMA toolkits and deliver one free physical kit
directly to inventory. Ordinary kits can still be looted, bought, carried and
crafted; possession alone never grants AP permission. Native recipe inputs,
parts, money, condition requirements and workshop/recipe permissions still apply.

| AP reward | Native section | Pool option | Additional use requirement |
|---|---|---|---|
| Tool Use: Basic Tools | itm_basickit | rewards_progressive_tools | None |
| Tool Use: Advanced Tools | itm_advancedkit | rewards_progressive_tools | Basic permission |
| Tool Use: Expert Tools | itm_expertkit | rewards_progressive_tools | Basic and Advanced permissions |
| Tool Use: Drug-making Kit | itm_drugkit | rewards_drug_making_tools | Independent |
| Tool Use: Gunsmithing Tools | itm_ammokit | rewards_gunsmithing_tools | Independent |
| Tool Use: Artefact Melter | itm_artefactskit | rewards_artefact_melter | Independent |

Each enabled reward is budgeted once before filler. The Basic/Advanced/Expert
chain preserves progressive use and the existing progressively later placement
rules for Advanced/Expert. Receiving Expert first supplies its kit but does not
skip Basic/Advanced permission. Specialist kits do not depend on this chain.
Disabling a category leaves that category's native kit use unrestricted.
The fresh melter permission is independent of general repair-equipment access;
its artefact checks retain detector and regional source requirements.

These replace the three AP coordinate-based orange tool stashes and the older
physical melter reward for fresh contracts. Native orange stashes and ordinary
acquisition remain intact. There is no Cordon visit requirement for the free kit.
`permission_supplies` does not disable this kit grant. A second receipt of the
same permanent permission never delivers another free kit.

## Repair-grade checks and crafting

The AP solver, PDA blocked reason and game check observer require Basic for
firearm repair grades A/B, Advanced for C, and Expert for D when progressive
permissions are enabled. These are check requirements; a rifle remains usable
under its permitted equipment class. Fresh class checks also use the configurable
condition threshold and toolkit requirements described in equipment classes. Existing grade D northern/psi or AP-goodwill
requirements also remain in effect. An Advanced permission cannot be placed
behind a grade C check that requires it.

The active recipe's input toolkit index determines crafting permission. The
output item does not: crafting a locked kit is allowed when its actual recipe's
input kit is usable. Inventory custom-use and the six native
`workshop_tool.start_workshop_*` shortcuts check kit permission before delegating.
Existing repair, upgrade and crafting mutation guards remain in place. Wrappers
read the central save through the coordinator; they own no progression state.

## Delivery and compatibility

New published item IDs 28051831–28051836 carry these permissions. Existing IDs
retain their meanings. Omitted `tool_use_permissions` is zero, retaining older
physical-stash/melter contracts and their manifests, digests and save semantics.
The new specialist toggles also default to zero when absent. New seeds default
to the new contract; Full Story enables both specialist categories. Matching
world, companion and add-on bundles are required. Switching an active seed's
configuration is unsupported; no existing session is changed by source work.

The existing central-save delivery plan creates the kit before granting its
permission or acknowledging the receipt. Definite creation failures retry;
uncertain creation blocks automatic replay and requires recovery. Save/load
retains the cursor. Loading an older save restores its receipt state and can
replay a kit with the native inventory rollback. Item creation and saving are
not atomic; crash-proof exactly-once delivery is not claimed.

## Source evidence and native acceptance

Read-only inspection of the active Archipelago DEV profile found the six toolkit
indices in `G.A.M.M.A. Artefacts Reinvention/workshop_tool.script`, crafting
requirements in its `craft.ltx`, the active `Serious Workshop optimization`
workshop override, and `139- Craft and Repair Overhaul` tool definitions.
`itm_ammokit` is the active Gunsmithing Tools section. Repair recipes use Basic
for pistol/shotgun, Advanced for rifle_5, and Expert for rifle_7. Source inspection
and mocked engine tests do not prove native behaviour.

In-game acceptance is **not run**, reserved for Owen. Test all six looted kits
before/after their AP rewards, crafting locked output kits, field/technician
repair and upgrades, actual grade C check/PDA state, one free kit per reward,
save/load, and late wrappers from other enabled mods. No deployment, game launch,
save write, developer-panel change or normal-game modification is part of this PR.
