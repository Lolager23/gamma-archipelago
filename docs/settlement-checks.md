# Step 08: major settlement checks

Stack base: all-map PR #11. The independent `checks_settlements` option adds
18 finite first-entry locations, IDs 28052101–28052118. It works alone or with
map checks, producing 18, 33 or 51 total checks with an exactly matching item pool.
The slot manifest, companion validation and game output use only enabled categories.

The roster is Rookie Village, Old Farmstead, Southern Checkpoint, Clear Sky Base,
Garbage Train Depot, Agroprom Research Institute, Agroprom Factory, Bandit Base,
Rostok, Freedom Base, Sakharov Bunker, Mercenary Base, Sin Mine Barracks,
Monolith Cultural Center, Skadovsk, Yanov Station, Hermann Bunker and Laundromat.
Faction hostility does not silently remove a hub from the generated roster.

New generations apply [settlement reputation access](settlement-reputation.md):
supported hostile bases require neutrality, and unsupported routes are filler-only.
All eighteen published checks remain in the roster. Legacy configurations retain
their original entry behaviour through the default-zero compatibility setting.

Entry uses Anomaly's `actor_on_interaction("smarts", object, name)` callback.
In the inspected `smart_terrain.script`, the online smart terrain calculates its
distance from the actor and emits this event at 50 metres or less. The add-on
also validates the expected map, smart name, online object and finite nonnegative
distance. Catalogue aliases for Rostok's bar/Duty areas and the Laundromat entrance
share a single location. No guessed coordinate is used. The radius is the engine's
existing smart-terrain volume; this is not a claim to match every building boundary.
Rosters and aliases were checked against smart names, simulation assignments and
smart configurations in the pinned baseline. Engine acceptance remains pending.

Checks are saved as a set, so overlap, repeated updates and re-entry do not award
duplicates. Server-confirmed checks are filtered through the enabled manifest
before reconciliation. Goal map observations have their own saved set, allowing
the pilot tour to complete even with map checks disabled. Existing saves without
that field migrate from their stored map checks. Legacy pilot seeds keep their
three-check output and cannot emit settlement checks.

The full verifier passes 377 covered tests plus two actual AP server cases, with
100% owned Python line/branch and Lua executable-line coverage. Tests exercise
every hub/alias, category combinations, boundary/outside distances, wrong map,
missing/offline objects, dead actor, malformed confirmation, save/load and goal
independence. Lua branch coverage is not measured. Live physical entry, callback
timing and actual volume placement are **not run**, reserved for the user's
post-merge verification. No game launch, deployment or protected-root write.
