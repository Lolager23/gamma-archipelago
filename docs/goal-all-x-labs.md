# Step 26: visit all named laboratories

Stack base: #29. Goal `all_x_labs` has a frozen five-level roster: X18
(`l04u_labx18`), X16 (`l08u_brainlab`), X19 (`l10u_bunker`), X8 (`labx8`) and
War Lab (`l13u_warlab`). The installed level roster is authoritative; ordinary
underground levels, Sarcophagus and Monolith Control Center are not laboratories
in this goal. The MCM displays the roster in plain text.

Actual level arrival records visits independently of enabled network map checks.
All five saved visits are required, in any order; repeats and reload do not reset
progress. Merely receiving keys or reaching other underground areas does not
qualify. The AP solver requires access to all five plus ordinary/local calibrated
protection. Visiting a lab means entering its level, not finishing every room,
door puzzle, document task or device inside it. Native restrictions remain active.

All six goal choices, fourteen check categories and seven reward categories now
have adapters. This does not mark their deferred in-game acceptance complete.
Full verifier: 513 covered tests plus two real-server cases, all independent
coverage gates pass. Tests include maps-off visits, wrong underground levels,
save/load between labs, roster parity and independent generation. Lua executable
lines measure 100%; branches are not measured. Engine lab arrival/goal acceptance
is not run, reserved for Owen. No launch or deployment occurred.
