# Practical progression expansion

Requested 21 November 2026. This is source work for new generations, stacked after
PR #69. No current seed is refilled, deployed or reset. Owen owns native testing.

## Increment 1: playability and placement

- Cap knife-only assumptions at five distinct mutant discoveries and 25 total
  kills. Faction kills and named mutants outside the five supported weak species require
  firearms.
- Paid AP shop contracts show their assigned reward automatically. They accept
  progression even under the default fragile-check policy. Expedition contracts
  costing 15,000 RU cannot hold GAMMA equipment permissions. Ordinary keys remain
  eligible. Mortality of a trader is still a native risk.
- Use AP-granted faction goodwill as the agreed rank proxy, never a sum of
  unrelated factions or native kill-earned rank. Required single-faction goodwill
  for Trainee through Legend is 250/500/750/1,000/1,500/2,000/3,000. Actual native
  rank thresholds remain required to trigger checks. Reserve twelve Free Stalker
  rewards when those checks are enabled; unsupported no-reputation routes are
  filler-only. Faction-standing checks use their own 500/1,000/2,000/3,000 values.
- Heavy/exoskeleton checks require calibrated psi protection, Red Forest access
  and a region beyond it, or 2,000 AP-earned goodwill with one faction as a trader
  access proxy. Class D receives a separate check; published pistol/rifle/etc IDs
  keep their meanings.
- Equipment permissions use low-grind checks within two map transitions of the
  selected start in activity pools. Sparse maps-only custom worlds retain their
  existing route-safety fallback. They cannot be placed at artefact 15, late rank, upgrades,
  story-chain walls or expensive shop contracts. This targets the first hour or
  two; no uncalibrated clock guarantee is claimed. Common AP constraints can make
  a requested pool impossible and must fail clearly rather than break logic.
- Fresh `playability_logic` defaults on; omitted old fields mean zero. Existing
  IDs and configuration identity for older seeds remain stable.

## Increment 2: content and progression contracts

- Add emission/Psi Storm experience checks through inspected native callbacks.
- Add an orange tool stash per tier. Progressive Tools supply physical basic,
  advanced and expert tools, with higher tier acquisition modelled at later
  access. Keep receipts and uncertain-spawn handling in the existing state owner.
- Keep artefacts distinct: 1–20 ordinarily progression-eligible; 21–40 require
  the melter; 41–60 exist only when needed for non-filler capacity. Never promise
  unsupported/quest-only types as reliable random spawns. Explain roster sources
  and show examples in the generator.
- Separate Mortal Sin and Operation Afterglow check toggles and completion goals;
  preserve preceding story requirements and legacy IDs.
- Add opt-in infinite stamina, off by default, using the supported native API.
- Audit X18/X16/X19 routes: Brain Scorcher is X19/Radar, using the native
  `bar_deactivate_radar_done` flag. X18 must not be substituted for X19.

## Increment 3: generator and analysis

- Add quantity sliders and numeric entry for repeatable rewards. The slider has
  a convenient suggested range; typed counts may exceed it. A finite check pool
  and the existing 4,000-receipt safety limit still bound valid generation.
  Truly infinite rewards cannot fit a finite AP seed.
- Retain mandatory progression before optional counts; reject overfull requests
  without silently dropping required items. Expose resolved counts and capacity.
- Limit each analysis step to one tier per equipment/knife/tool chain. Checks
  deferred by this assumption remain listed for the next step; this is a pacing
  model separate from AP's actual logical spheres and native completion.
- Update the local calculator, source explanation and ten-seed analysis. The
  historical visualizations retain their original archived placements.

Each increment needs source review, regression/coverage, real generation/server
verification, exact-head Windows/Linux CI and retained package hashes. Native
acceptance stays **not run** until Owen reports results. None of these increments
authorizes a merge, deployment, session reset or game launch.

Stage 2 implements weather checks, split story goals, tiered physical tool stashes,
melter access, late equipment check gates and opt-in stamina. See
[content progression](content-progression.md) for exact contracts and native limits.
Conditional artefact overflow and quantity controls remain the next increment.
