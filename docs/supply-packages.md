# Step 37: useful supply packages

Stacks on permission-supplies PR #45. Four independent APWorld toggles add useful
optional rewards: `rewards_supply_medical`, `rewards_supply_maintenance`,
`rewards_supply_ammunition` and `rewards_supply_expedition`. All default off.

| Package | Contents | Relative optional-pool weight |
|---|---|---|
| Medical | 2 army medkits, 1 scientific medkit, 2 bandages, 1 antirad, 1 morphine, 1 antidote | 3 |
| Maintenance | 2 gun oils, 2 solvents, 2 advanced adhesives, 1 heavy sewing kit, 1 duct tape | 2 |
| Ammunition | Three native boxes of the selected calibre | 3 |
| Expedition | Bread, drinking water, bandage | 2 |

The 27 November improvement gives each named medical/maintenance package eight
objects. These are direct inventory deliveries, independent of stash value/cash.
Native charges, item behavior and inventory-repair rules remain unchanged. The
separate single-item medical/maintenance filler rewards retain their own contents.

Previously started packages retain their exact saved version-1 plans: medical
was one basic medkit, bandage and antirad; maintenance was one gun oil, advanced
adhesive and duct tape. The catalogue retains those `legacy_supplies_v1` sections.
New plans for these two IDs store `version=2`; load validation and copying preserve
that version. A partial old plan completes its remaining original items, and the
next receipt uses the new eight-item plan. Already-delivered packages are not
backfilled or restarted. Unsupported plan versions are refused before mutation.
There is no item-ID, seed, receipt-order or configuration-digest change. Downgrading
a new plan requires the matching pre-update save/bundle backup.

`supply_ammo_calibre` selects 9x18 (default), 9x19, 5.45x39, 5.56x45 or 7.62x39.
Box sizes come from active native definitions; this does not promise a fixed
round count or detect the player's equipped weapon. Choose the calibre to suit
the intended character. Sections were checked in the extracted native definitions
and are preflight-checked again before spawning in the game.

These packages are useful filler, not required progression. They never displace
mandatory permissions. The optional reward draw uses relative catalogue weights;
this is not a guaranteed percentage of the entire seed. The existing optional
reward frequency remains one initial optional draw and roughly one in three
eligible later filler slots. Small pools still fit one item per check. Eligible
types are previews of possible rewards, not guaranteed quantities of each type.
When packages are disabled, the old uniform optional reward selection retains
its original random-number path.

Packages use the saved bounded delivery plans from [Step 36](permission-supplies.md)
with at most one created object per poll. Each new package receipt deliberately
grants a fresh package; duplicate packets for an applied receipt cannot repeat it.
Partial save/load resumes its cursor. Uncertain creation blocks automatic retry.
The PDA labels it `package pending`, and acknowledgement waits for all contents.
Permission supplies remain independent and can be disabled for package-only seeds.

Four new item IDs are added; existing IDs, receipt formats, optional save records
and default configuration identities retain their meaning. New non-default
categories/calibres require a fresh seed and coordinated world/client/add-on.

Native verification is **not run**, reserved for Owen: actual GAMMA item/box
quantities, calibre usefulness, economy, partial delivery/reload and PDA status.
Weights and contents are initial tuning values, not measured balance results.
No game launch, deployment, installed-game write or developer-panel change is
included.

The final stable-source complete verifier passed: 938 covered tests, 38 untraced
generator/server tests and five Node tests (981 total), including 100 filled
package/minimal-pool seeds. Owned Python runtime modules reached 100% measured
line/branch coverage; Lua reached 100% measured executable lines. Lua branch
coverage is not measured. The workbench correctly refused an earlier stale
runtime after a base-doc merge restored checkout line endings; the final run
rebuilt the matching runtime and passed the actual web generation tests.
