# Step 19: optional starting equipment permissions

Stack base: #22. All nine starting gear groups support normal (0), initially
absent (1), or AP-locked (2). AP mode requires the unlock reward category; that
category requires at least one selected lock. Only selected permissions enter the
required progression pool. Every unlock includes a usable baseline section.

Mode 1 retains step 6's omission-only behaviour. Mode 2 also vetoes native pickup
and use, returns scripted/purchased/crafted locked inventory to the ground through
`drop_item`, and checks remaining inventory in bounded batches. It does not delete
that later loot. Permission is saved before its baseline grant, allowing native
callbacks to accept the baseline. Missing sections and nil creation remain
pending; creation exceptions persist an uncertain outcome and block automatic
retry. A lock enforcement failure does not prevent its key from being received.

The pinned native pickup binder reuses its callback flags without resetting them.
A delegating wrapper clears stale flags before each new dispatch, so one denied
locked pickup cannot block later allowed items. Vetoes from other mods in the
current dispatch remain intact. Locked seeds refuse an unavailable pickup hook.

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
