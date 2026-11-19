# Step 18: quest progression permissions

Stack base: #21. Three required AP items unlock Living Legend, Mortal Sin and
Operation Afterglow. All 83 frozen task aliases in those chains are gated at the
native `CRandomTask.give_task` assignment method. This is an explicit delegating
wrapper because the installed engine has a completion callback but no cancellable
assignment callback. Other wrappers retain their captured delegate; ordinary side
tasks and seeds with the option disabled pass through unchanged.

Locked native requests are saved with their giver and replayed through the
original method after permission, at most one per poll. Assignment is acknowledged
only when native task state exists. Failures remain pending; already-created
assignments are not duplicated. Initial requests survive the fresh-character
load callback. Keys never fabricate objectives, story info portions or completion.
The native story still owns NPCs, prerequisite flags and quest completion.

Solver story checks require the matching key and permissions for every earlier
native chain: Mortal Sin needs Living Legend, and Operation Afterglow needs both.
The native dialogue conditions require the earlier chain's completion flags;
including these key dependencies prevents placing an earlier key behind a later
story check. Native story completion itself remains the game's responsibility.
Every enabled key is placed exactly
once. Story-only checks with quest keys are rejected because all would sit behind
their own permissions. A pool smaller than its required items is also rejected.
Quest keys must be selected for a fresh story-enabled character; importing an
already-active chain is not a supported way to retroactively undo story progress.

Full verifier: 468 covered tests plus two real-server cases, 100% measured Python
lines/branches and Lua executable lines. Tests cover deferral, repeated requests,
initialization, save/load, missing manager, side effects, unconfirmed assignment,
wrapper composition and solver access. Lua branch coverage is not measured.
Engine story scheduling/dialogue behaviour is not run, reserved for Owen after
merge. No game launch, deployment or protected-root changes occurred.
