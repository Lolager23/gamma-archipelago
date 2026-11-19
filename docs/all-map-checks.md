# Step 07: all supported maps

Stack base: starting-loadout PR #10. New seeds contain one First Arrival check
for each of the 33 playable level identifiers in the pinned baseline. Cordon,
Garbage and Rostok retain IDs 28052001–28052003. The other maps receive stable
IDs 28052004–28052033. `fake_start` is excluded. The catalogue publishes the
human names and level identifiers, including distinct Pripyat/Outskirts and
CNPP South/North entries. War Lab is not labelled as Lab X8.

Each level has an AP region connected through the documented overland and
underground topology. The current goal remains the three-map pilot tour; adding
30 exploration checks does not silently change the goal. The item pool contains
the existing three rewards plus enough Bandages to fill every location. All
regions are traversable in the solver at this step: ordinary story/protection
requirements are not replaced by AP permissions until the later gate/goal PRs.
The topology was compared with `game_levels.ltx`, the guide routing tables and
the installed extra-transition implementation. The guide's northern/underground
table is commented reference data, so this is not evidence that every runtime
transition or MCM-dependent extra route has been exercised. Full route enforcement
and progression prerequisites belong to the zone-key branches.

New seeds use slot schema 3 with an explicit location manifest and configuration
snapshot version 2. The companion rejects a mismatching manifest before publishing
it, binds it for the session and rejects disabled or unknown checks. Slot schema
1 and 2 seeds retain their three-map manifest and original goal. The game saves
the expanded-mode marker; legacy snapshots filter out additional catalogue IDs.
No published IDs are reused. A newly expanded seed requires a separate save/session.

Verification passes 364 covered tests and two actual AP server cases, including
all 33 checks, receipt replay, mixed APQuest traffic and server restart. Owned
Python line/branch and Lua executable-line coverage are 100%; Lua branches are
not measured. One thousand deterministic exploration seeds fill and complete in
the AP solver. Mocked-engine tests cover every identifier, repeat visits, save
copies, legacy filtering and configured adapter polling.

Live game arrival on the additional maps, actual route availability and transition
timing are **not run**, reserved for the user's post-merge acceptance. No game
launch or installed add-on change was performed for this step.
