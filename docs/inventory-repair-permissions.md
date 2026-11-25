# Inventory repair permissions

Inventory repair consumables do not use Basic/Advanced/Expert workshop tools.
Their native repair dialog is exempt from AP tool and workshop restrictions.
The exemption also covers using such consumables under the older generic Tools
equipment lock. Workshop/technician repairs and upgrades, crafting and the six
AP toolkits retain their existing permission rules.

## Native classification and delegates

The adapter queries native `IsItem("repair", section)`, whose Anomaly `Parse_ITM`
registration comes from `repair_tool` and stores either `true` or the `repair_only`
target table. It uses the actual repair object's section, not a display label.
Missing/unsupported registry data does not grant an exemption. Basic, Advanced,
Expert, Drug-making, Gunsmithing and Artefact toolkits are explicitly excluded
using existing catalogue definitions, even if another mod labels one as a repair
consumable. Unrelated tools and equipment permissions remain restricted.

The `item_repair.UIRepair.OnRepair` wrapper delegates recognised consumables
without AP permission checks. The captured native method still owns eligible
targets, condition, supporting supplies, repair effects and item consumption.
AP does not implement a second repair transaction. Ordinary inventory tools are
also exempted at the shared gear-use guard. A weapon with a repair action retains
its weapon/equip restriction; the exemption only relaxes a generic Tools lock.

Source inspection covered pinned Anomaly `_g.script` / `item_repair.script`,
GAMMA's enabled `143- Keep Crafting Window Opened` replacement, `G.A.M.M.A. UI`
technician repair and the toolkit entry points in Craft and Repair Overhaul.
Native repair items include gun oil, cleaning kits and sewing kits; new native
repair consumables can qualify without changing an AP allowlist.

## Compatibility and acceptance

No item/check IDs, slot settings, receipts, save schema or seed placements change.
This stacks on the equipment-check tool-independence change. Existing saves need
no migration when the updated add-on is deployed. This source PR does not deploy,
launch GAMMA, alter the developer panel, switch the current session or write to
the protected normal installations. Native acceptance remains Owen's: use ordinary
repair supplies before any tool/workshop reward, confirm native costs/condition
checks, retry after save/load, and confirm actual toolkits/workshop actions remain
locked until their permissions arrive.
