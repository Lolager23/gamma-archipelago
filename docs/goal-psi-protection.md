# Step 22: calibrated psi-protection goal

Stack base: #25. Goal `psi_protection` completes only after the actor actually
possesses usable `good_psy_helmet` protection. A bad/uncalibrated helmet, received
coordinates or quest permission alone is insufficient. The native radar logic
and phantom manager use this calibrated section. Condition must be numeric and
in (0,1]. Inventory API failure refuses goal reporting. Observed completion is
saved and monotonic after later item loss/reload.

The solver models ordinary calibrated acquisition as a local Yantar/Sakharov
event, or the protected orange cache's separate local claim. Local events have
no network IDs and consume no item slots. Ordinary acquisition assumes normal
earnable money and completing calibration; the add-on does not bypass that task.
Alternate goals use outgoing protocol 2, selected by the validated configuration.
Pilot protocol 1 retains its three-map validation. An alternate victory can be
reported without pilot checks; mismatched protocol/goal selection is rejected.

Zone keys retain the guaranteed local exploration chain from step 20, which
corrected circular placement in map-only seeds: shuffle the reachable
frontier and place its key in the previous visited map's first-arrival check.
Return paths allow backtracking to any already-open frontier. Yantar precedes
psi-gated maps. Every key remains an AP receipt/check, but zone keys are local to
their GAMMA slot; other rewards retain ordinary multiworld fill. This explicit
constraint guarantees finite exploration rather than relying on general fill to
break cycles. Previously failing seeds 1/4/5/22 are regression cases.

Full verifier: 504 covered tests plus two real-server cases; all owned measured
Python lines/branches and Lua executable lines are 100%. Tests cover inventory
qualification, goal protocol binding, local event/pool separation, reload and
key-chain reachability. Lua branches are not measured. Engine calibrated-helmet
and goal-packet acceptance are not run, reserved for Owen. No game was launched.
