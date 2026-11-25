# Step 35: workshop and recipe access

Stacks on Progressive Tools PR #43. Two independent APWorld toggles, off by
default, add the following permissions:

| Option | Required pool entries | Native actions |
|---|---|---|
| `rewards_workshop_access` | Repair, Upgrades, Crafting | The corresponding workshop, toolkit and technician mutation entry points |
| `rewards_recipe_access` | General, Medical, Ammunition, Artefacts | Crafting recipes using native toolkit indices 1–3, 4, 5 and 6 respectively |

These permissions unlock access to known recipes/actions. They do not grant all
encyclopedia recipe knowledge or waive ordinary parts, toolkits, money and native
requirements. In particular, a recipe book does not bypass an AP recipe-group
permission. Progressive Tools remains independent: when both systems are on,
both the action/group permission and its relevant tool tier are required.

Ordinary [inventory repair consumables](inventory-repair-permissions.md) are
exempt: their native dialog needs neither Workshop Access: Repair nor Basic Tools.
The native item/condition/supply checks and consumption remain authoritative.

For fresh content/playability activity pools, all three workshop permissions now
use the [early equipment allocation](early-equipment.md). Local rewards arrive
through nearby, currently reachable low-grind checks before unrelated zone-key
or rank chains. Non-local workshops use upstream early-item requests. Existing
gifts/plando and sparse exploration fallback remain authoritative. This is an
early capability guarantee in the tested local configurations, not measured hours.
Recipe-group access and progressive tool tiers remain separate reward systems.

All seven permissions are progression rewards and are budgeted before filler.
The solver and PDA require `Workshop Access: Upgrades` for upgrade checks. Repair
and crafting permissions remain useful gameplay restrictions even when no enabled
check directly requires them. No new checks or infinite crafting item farm is
introduced. There is no additional restriction when both options are disabled.

The existing workshop guard validates supported mutation methods and delegates
permitted operations to the captured native function. It reads selected recipe
metadata immediately before crafting. Unknown actions or unsupported recipe
requirements refuse before native mutation. Permissions use the existing central
saved unlock set and receipt/save history. No extra state owner, item spawn or
native recipe registry is introduced.

The supported baseline is the installed GAMMA workshop override inspected in
[Progressive Tools](progressive-tools.md). Other crafting mods exposing a different
action path require an explicit adapter; community examples do not establish that
they are guarded. Missing baseline methods report a refused integration. This is
source and mocked-boundary evidence; native compatibility is unverified.

Existing IDs and default configuration identities are preserved. Seven new item
IDs are added, and non-default settings require a new generated seed with matching
world/client/add-on. Old saves need no schema change; new permission keys already
use the catalogue-generated validated unlock set.

Native acceptance is **not run**, reserved for Owen: all workshop/field/technician
routes, each of the six toolkit-index recipe groups, native book/parts checks,
independent options, progressive-tool combinations, refused action feedback and
save/load. No launch, deployment or installed-game changes are included.

The complete verifier passed: 902 covered tests, 37 untraced generator/server
tests and five Node tests (944 total), including 50 filled combined-permission
seeds. Owned Python runtime modules reached 100% measured line/branch coverage;
Lua reached 100% measured executable lines. Lua branch coverage is not measured.
One earlier covered run failed an existing pickup-guard case once. The focused
suite, 32 repeated fresh-session transitions and the final complete suite passed;
the case remains enabled with failure diagnostics. No root cause is claimed.
