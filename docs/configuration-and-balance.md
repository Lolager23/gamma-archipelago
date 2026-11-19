# Step 27: presets and generation matrix

Stack base: #30. Six editable YAML presets cover the development tour, exploration,
a 33-map MVP with the Scorcher goal and PDA/detector locks, full story, full labs,
and an intentionally restricted start. `src/gamma_archipelago/presets.py` is their
validated definition. Defaults keep ordinary food/medicine/ammunition available;
only the explicitly restricted preset reduces supplies and omits starting weapons.
Starting omission never removes subsequently earned ordinary equipment.

The matrix generates 1,000 seeds for each preset, checks all fourteen check and
seven reward categories individually and in pairs with their documented
dependencies, and exercises every goal against full options. It verifies finite
pool counts, complete placement, beatability and reachability. These are solver
tests, not evidence of a pleasant difficulty curve or in-game spawn availability.
The large repeated matrix runs without tracing after the covered regression pass;
every case still runs in the fail-fast verifier and both CI platforms. No owned
runtime module or coverage gate is excluded.

With progression stashes enabled, ordinary calibrated helmets cannot bypass the
orange cache claim: native pickup/use is vetoed and direct grants are returned to
the ground until that claim grants permission. The solver removes the ordinary
Sakharov acquisition event in this mode and requires the local cache claim for
psi-gated access. With the category off, native acquisition remains unchanged.
The native pickup guard also applies to psi-only locks, resetting the binder's
reused flags before each dispatch so a rejected helmet cannot block later loot.
An uncalibrated helmet retains its native limited protection; it does not satisfy
the calibrated goal. AP does not turn it into calibrated protection.

Zone keys are local randomized exploration-chain rewards. Other items use the
ordinary multiworld pool. Combining that chain with exclusive psi coordinates
requires settlement checks, providing early unreserved slots for coordinates and
a locked PDA. Required rewards must fit the chosen pool. All map checks on the
zone chain must remain included; explicit exclusion is rejected. Invalid settings
raise an explanatory generation error rather than silently enabling a category.

Useful/filler balance is a first playtest baseline: native food/basic medicine
remain available, optional loot/reputation/skills supplement ordinary scavenging,
and permission items are placed once per selected lock. Actual difficulty,
equipment quality, stash geometry and time-to-progression remain for Owen's
post-merge playtests. Native ALife encounters and task/NPC availability are not
guaranteed by a solver reachability result. No game launch or deployment is part
of this matrix.

The complete verifier passes 581 covered regression/integration tests and eight
untraced cases (six 1,000-seed presets and two real-server sessions). Every
independent coverage gate passes. The matrix also covers 231 category singles/
pairs and 60 full-option goal seeds. Engine acceptance remains not run.
