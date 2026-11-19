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

PDA notices remain queued without a device. Local stash opening also requires
an available PDA, and the solver's protected cache claim requires the PDA unlock
when AP-locked. A permission cannot be hidden behind that same local stash claim.
The generic pool-size guard rejects required permissions exceeding network checks.
The later balance matrix tightens other equipment-dependent activity rules.

Full verifier: 474 covered tests plus two real-server cases; all independent
coverage gates pass. Tests cover omission, native pickup/use, scripted inventory,
failed dropping, saved permissions, baseline failures/uncertainty and PDA solver
access. Lua executable lines measure 100%; Lua branch coverage is not measured.
Actual inventory/UI enforcement and animations are not run, reserved for Owen.
No game launch, deployment or protected-root changes occurred.
