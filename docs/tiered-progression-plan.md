# Equipment classes and quest-safe progression

Requested 22 November 2026. Source work stacks after #76. Existing session archives,
installed Dev files, the private developer panel and normal installations remain
unchanged. Native acceptance belongs to Owen; agents do not launch the game.

## Delivery increments

1. Quest travel: mirror the active northern psi field's X16 and X19 shutdown
   requirements, carry the Living Legend/Agroprom route into the shutdown event,
   and use actual access rules for sparse key planning. Reproduce New 04's
   Agroprom-at-Generators dependency and validate fresh generation. Preserve old
   omitted-field configuration identities and archive behaviour.
2. Class permissions: replace binary firearm/outfit/backpack permissions for fresh
   contracts with cumulative class progression. Start at A/Novice by default,
   configurable down to zero. Give free backpacks at each unlocked tier. Always
   supply and permit a knife; keep cumulative knife upgrade checks. Restrict the
   native creation inventory to AP-selected permissions. Convert tools to generic
   Basic-to-Expert receipts. Add configurable equipment condition thresholds,
   default 65%, and corresponding repair-tool requirements in logic.
3. Activity and reward balance: cap generic mutant logic at five opening types
   and at most two additional supported types per region. Require Advanced tools,
   Medium armour and Class C for Scorcher; Expert, Heavy and Class D for Path
   Pripyat. Require Scorcher and a region beyond Red Forest for machineguns and
   exoskeleton checks. Require artefact recipes for discoveries 21–40. Add an
   optional artefact reward category. Update generator controls and step reports.

Each increment needs meaningful regressions, the complete verifier, the unchanged
9,000-seed matrix, real AP generation/server passes, current-head Windows/Linux
CI and retained package hashes. PRs remain draft while native acceptance is open.

## Placement model

Archipelago randomizes rewards using our region, entrance and check access rules.
It does not read GAMMA quests. Local logical events represent achievable native
shutdowns without adding network rewards or automatically completing game quests.
The item filler must be able to reach a proposed key's location while excluding
that key; therefore Agroprom cannot be placed at Generators when Generators needs
Scorcher, whose story route needs Agroprom. Real game facts still determine check
completion. Sphere/step reports are predictions from these declared rules, not
native proof or measured playtime.

The installed northern psi script requires both `yan_labx16_switcher_primary_off`
and `bar_deactivate_radar_done` for Free Stalkers in story mode. Northern access
is therefore stronger than owning a calibrated helmet. Source evidence and New
04's archived placements are retained privately outside Git.
