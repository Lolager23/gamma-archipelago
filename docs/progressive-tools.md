# Step 34: progressive tool permissions

Historical increment: fresh contracts now use generic receipts with guaranteed free
kits under [equipment classes](equipment-classes.md). The permission-only behaviour
below remains supported for configurations omitting those new contract flags.

Stacks on discovery PR #42. APWorld `rewards_progressive_tools` is off by default.
When enabled, the pool includes three copies of the new `Progressive Tools` item.
Their applied receipt order unlocks Basic, Advanced and Expert permission. Copies
beyond the third are capped. These are permissions; physical tools, parts, recipe
knowledge, money and the native condition requirements still apply. Ordinary
acquisition cannot substitute for an AP permission. Attached supplies are a later
independent option, not an implicit toolkit grant here.

The add-on guards mutation entry points for workshop repair, workshop upgrades,
crafting, toolkit repair and technician repair/upgrades. Workshop repair requires Basic;
one-chevron upgrades require Basic, two require Advanced, and three require Expert.
The selected native upgrade metadata determines difficulty, including GAMMA's
class-based remapping. Recipes using the first three workshop toolkit tiers
require their corresponding permission. Drug, ammunition and
artefact kits remain separate native systems in this step. No inventory is
stripped. Disabling the option leaves ordinary native actions unrestricted.

Inventory maintenance items recognised by Anomaly's native repair-item registry
are exempt from tool/workshop permissions. Gun oil, cleaning and sewing kits
therefore retain ordinary native use without Basic Tools. The six AP toolkits are
never exempt. See [inventory repair](inventory-repair-permissions.md).

The AP solver and PDA require Basic before aggregate installation-count checks:
several one-chevron upgrades, including upgrades on different items, can satisfy
them. The native observer uses the same minimum and retains the configured item
condition threshold. Higher difficulty still requires the corresponding applied
permission before the action. Permissions are placed as progression and three
copies are budgeted before filler. A pool too small for those copies rejects generation instead of truncating
them. All other gates and starting-equipment options continue to apply.

## Ownership and compatibility

The tool level is derived from the central save's applied item history. There is
no separate mutable tool counter, ordinary-item detection or network/UI state
owner. A received file is insufficient; permission appears only after the receipt
is applied. Save/load and older-save rollback use the existing ordered-history
reconciliation. No consumable is created, so granting this permission introduces
no additional spawn/save crash boundary.

Hooks wrap the active methods after game initialization and recheck on bounded
polls. Captured delegates compose with other wrappers; all required methods are
validated before changing them. Unknown recipe requirements refuse the action.
Missing integration APIs prevent receipt processing with an actionable error.
This establishes supported-source guards, not proof of compatibility with every
third-party script that can mutate equipment.

Source inspection found the active `Serious Workshop optimization` profile
overrides `ui_workshop` and separately patches `Repair` and `Craft`. The supported
entry points are `UIWorkshopRepair.Repair`, `UIWorkshopUpgrade.Upgrade`,
`UIWorkshopCraft.Craft`, `item_repair.UIRepair.OnRepair`, and inventory
`RMode_RepairYes`/`RMode_UpgradeYes`. Selected recipe `tool` values map to the native
six-entry workshop toolkit list. Base-script replacement is not used.

New zero defaults preserve existing configuration digests. Generated native
defaults now come from the same bounded core definitions as Python. Existing
published IDs retain their meanings. New non-default settings require a fresh
seed and coordinated world/client/add-on upgrade.

Native acceptance is **not run**, reserved for Owen: active workshop and technician
routes, field repair, actual selected recipe tiers, ordinary tool acquisition,
physical supplies, late wrappers, permissions at all three levels, and reload.
No deployment, launch or installed-game write is part of this change.

The complete verifier passed: 894 covered tests, 36 untraced generator/server
tests and five Node tests (935 total), including 50 filled progressive-tool seeds.
Owned Python runtime modules reached 100% measured line/branch coverage; Lua
reached 100% measured executable lines. Lua branch coverage is not measured.

## Fresh content progression

The later [content contract](content-progression.md) introduced named physical
tool stashes. Fresh seeds now use [tool-use permissions and free kits](tool-use-permissions.md),
including independent specialist kits. The rules above remain the compatibility
contract for older content_progression=0 sessions; content_progression=1 with
tool_use_permissions=0 preserves the physical-stash contract.
