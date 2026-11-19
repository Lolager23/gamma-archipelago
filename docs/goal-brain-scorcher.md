# Step 23: disable the Brain Scorcher

Stack base: #26. Goal `brain_scorcher` observes the native
`bar_deactivate_radar_done` info portion used by Radar/X19 restrictors. Merely
entering the bunker, receiving a key or obtaining protection does not complete
it. Missing native queries refuse victory reporting; only boolean true qualifies.
Completion is saved and monotonic through ordinary reload.

The solver requires calibrated protection and reaching X19, with a separate
local shutdown event. It respects zone entrances and ordinary Sakharov/orange
cache acquisition routes. No shutdown info is granted by AP rewards. Story mode
is not required for the standalone device goal.

Full verifier: 506 covered tests plus two real-server cases; all coverage gates
pass. Tests separate entry/key state from shutdown, reject non-boolean/missing
facts, retain reload completion and fill keyed seeds. Engine switch/goal acceptance
is not run, reserved for Owen after merge. No launch or deployment occurred.
