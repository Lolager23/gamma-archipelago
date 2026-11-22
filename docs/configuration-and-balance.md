# Step 27: presets and generation matrix

Historical stack base: #30. The original six editable YAML presets cover the
development tour, exploration,
a 33-map MVP with the Scorcher goal and PDA/detector locks, full story, full labs,
and an intentionally restricted start. `src/gamma_archipelago/presets.py` is their
validated definition. Defaults keep ordinary food/medicine/ammunition available;
only the explicitly restricted preset reduces supplies and omits starting weapons.
Starting omission never removes subsequently earned ordinary equipment.

The release matrix generates 1,000 seeds for each preset (currently ten presets,
10,000 seeds), checks the check and reward categories individually and in pairs with their documented
dependencies, and exercises every goal against full options. It verifies finite
pool counts, complete placement, beatability and reachability. These are solver
tests, not evidence of a pleasant difficulty curve or in-game spawn availability.
The large repeated matrix runs without tracing after the covered regression pass;
every case still runs in the full release verifier on both CI platforms. Normal
PRs use [affected verification](testing-policy.md). No owned
runtime module or coverage gate is excluded.

## Story tiers

| Preset | Story checks included | Victory |
|---|---|---|
| Living Legend (`living_legend`) | Living Legend; Mortal Sin and Operation Afterglow checks off | Finish Living Legend |
| Full Story (`full_story`) | Living Legend, Mortal Sin and Operation Afterglow | Finish all three chains, ending with Operation Afterglow |

Both use the same expanded equipment, exploration and reward settings. Other
categories and quest-key rewards remain independently editable. Living Legend
does not require either later chain's completion or permission. Full Story reuses
the existing Operation Afterglow goal: its solver events require Living Legend,
then Mortal Sin, then Afterglow, including each enabled quest-key permission.
The generator labels this as finishing all three story chains.

No numeric goal values or published IDs change. Existing exports, saved drafts
and running sessions retain their selected goal/checks. Applying a preset again
or generating from its new YAML uses the new definition. The original Full Story
goal of Living Legend is still selectable directly as goal 4.

With progression stashes enabled, ordinary calibrated helmets cannot bypass the
orange cache claim: native pickup/use is vetoed and direct grants are returned to
the ground until that claim grants permission. The solver removes the ordinary
Sakharov acquisition event in this mode and requires the local cache claim for
psi-gated access. With the category off, native acquisition remains unchanged.
The native pickup guard also applies to psi-only locks, resetting the binder's
reused flags before each dispatch so a rejected helmet cannot block later loot.
An uncalibrated helmet retains its native limited protection; it does not satisfy
the calibrated goal. AP does not turn it into calibrated protection.

Zone keys use ordinary AP fill in expanded regional pools, including multiworlds.
Only sparse exploration retains the anti-cycle route and its explicit map
exclusion/locality conflicts. Pool capacity and opening checks remain validated;
existing map/settlement category requirements still protect reliable regional capacity.
Invalid logical fills fail rather than silently enabling a category. See
[generation pacing](generation-pacing.md) for natural progression and limitations.

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
