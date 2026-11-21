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
Configured seeds use outgoing protocol 3, bound to the validated configuration
digest before checks or victory are accepted. Legacy pilot protocol 1 retains
its three-map validation. An alternate victory can be reported without pilot
checks; stale or mismatched configurations are rejected. Upgrade companion and
add-on together; existing saved receipts are unchanged. See the
[bridge protocol](bridge-protocol.md) for compatibility and snapshot ordering.

Zone keys now use ordinary AP fill in expanded regional pools, including multiworlds,
while psi-access prerequisites remain enforced. Only sparse exploration
retains the anti-cycle route from step 20, including Yantar before psi-gated maps;
previously failing seeds 1/4/5/22 remain regression cases. Keys can cross players
under normal AP settings. See [generation pacing](generation-pacing.md).

Full verifier: 504 covered tests plus two real-server cases; all owned measured
Python lines/branches and Lua executable lines are 100%. Tests cover inventory
qualification, goal protocol binding, local event/pool separation, reload and
key-chain reachability. Lua branches are not measured. Engine calibrated-helmet
and goal-packet acceptance are not run, reserved for Owen. No game was launched.
