# Step 19: optional starting equipment permissions

Stack base: #22. All nine starting gear groups support normal (0), initially
absent (1), or AP-locked (2). AP mode requires the unlock reward category; that
category requires at least one selected lock. Only selected permissions enter the
required progression pool. Every unlock includes a usable baseline section.

Mode 1 retains step 6's omission-only behaviour. Mode 2 omits initial gear, but
later locked gear can be looted, bought, carried, sold and maintained. Its AP
permission is required to equip/use it. Native UI guards deny equip/use actions;
post-slot callbacks and a fixed 13-slot reconciliation move locked equipment into
the actor's rucksack, preserving the object instead of dropping/deleting it.
Weapon press/hold guards prevent use while native deactivation is pending.
Menu-captured or engine-disabled input is left to its owner, preserving inventory
clicks and other UI controls while world weapon actions remain locked.
PDA entry, custom tool/device actions, device event consumption and NV activation
also read the same permissions. Native battery charging and gun/armour maintenance
remain available. Permission is saved before its baseline grant, allowing native
callbacks to accept the baseline. Missing sections and nil creation remain
pending; creation exceptions persist an uncertain outcome and block automatic
retry. A lock enforcement failure does not prevent its key from being received.

The calibrated psi device is a separate progression-stash permission, not an
equippable starting-gear group: native protection activates merely from carrying
it. Its pickup/purchase/use veto and bounded return-to-ground safeguard remain
until the orange stash is claimed. Ordinary locked gear is never dropped.

The pinned native pickup binder reuses its callback flags without resetting them.
A delegating wrapper clears stale flags before each new dispatch, so one denied
locked pickup cannot block later allowed items. Vetoes from other mods in the
current dispatch remain intact. Psi-stash seeds refuse an unavailable pickup hook;
ordinary equipment permissions no longer require that pickup-only mechanism.

PDA information and tracker access use device availability. Physical AP stash
opening and the solver's local protected claim do not require a PDA; they require
the received coordinate plan and the recorded native container instead.
The generic pool-size guard rejects required permissions exceeding network checks.
The later balance matrix tightens other equipment-dependent activity rules.

Full verifier: 474 covered tests plus two real-server cases; all independent
coverage gates pass. Tests cover omission, native pickup/use, scripted inventory,
failed dropping, saved permissions, baseline failures/uncertainty and PDA solver
access. Lua executable lines measure 100%; Lua branch coverage is not measured.
Actual inventory/UI enforcement and animations are not run, reserved for Owen.
No game launch, deployment or protected-root changes occurred.


## Random starting permission and activity logic

`random_starting_unlock` optionally grants one seed-random permission among the
AP-locked PDA, Firearms and Detector groups. Normal/omission-only groups and
permissions already requested through common AP starting inventory are skipped.
If every eligible lock is already precollected, there is no duplicate grant; no
eligible configured lock is an error. Firearms is the existing permission and
baseline weapon, not a new progressive weapon system.

The world precollects the selected item before pool construction. The shared pool
budget removes its mandatory network copy, and schema-4 generation identity binds
the actual starting gift. CommonClient delivers it through normal ordered starting
receipts; the game retains its permission/baseline failure and saving rules. A fresh
seed and character are required. The settings preview does not roll: it validates
all possible gifts, lists their budgets separately and shows the most demanding
remaining protected opening. Actual-seed reports contain the resolved gift.

AP rules and PDA blocked reasons now also require a locked PDA permission for
quest-type, side-task and story-milestone checks. Detector/artefact checks, firearm
and melee/kill alternatives, armour/weapon/knife checks, strict combat assumptions,
and workshop/tools gates retain their matching requirements. Normal or merely
omitted gear does not demand an AP unlock. Old generated placements are not refilled;
regenerate a seed to use corrected placement logic. Completed checks stay monotonic.

Upgrade checks can now observe improvements to carried guns, outfits or helmets
before equipping is unlocked. The ownership requirements introduced in PR #64 are
therefore superseded. AP logic and the PDA retain independent progressive-tool and
workshop requirements. Worn-armour, active-firearm and knife checks still require
their equip permissions; a pending native unequip cannot award them accidentally.

IDs, configuration bytes and saved permission/receipt formats are unchanged. Existing
matching saves retain their unlocks and can use the new runtime behaviour after a
coordinated deployment. New AP placement rules need a fresh generation; an existing
archive is never refilled. No extra item ledger or forced auto-equip is introduced.

Native acceptance remains not run for Owen: ground/box loot, mixed trader baskets,
context/double-click/drag equip, hotkeys and custom device/tool actions, scripted
auto-equip, old-save reconciliation, unlock arrival, battery charging and upgrading
stored equipment. Verify the private developer panel and ordinary purchases too.
UI/device wrappers preserve native return values, other wrappers and current vetoes;
warnings use translation-ready resources and the existing loading-readiness gate.
