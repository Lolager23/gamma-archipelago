# Reward quantities and paced seed analysis

Fresh seeds use explicit reward quantities. The legacy weighted pool remains an
option and old snapshots omit all new zero-valued fields. Mandatory permissions,
neutrality and rank proxy rewards are calculated first. Enabled repeatable groups
then contribute exact requested copies; ordinary Medkits/Bandages fill spare slots.
Medical, maintenance, ammunition and expedition packages default to four each;
Basic, Field and Advanced loot stashes default to four each; stat levels default
to nine and extra faction goodwill to zero. Disabled categories contribute none.
Physical Basic Toolkit copies have a separate count, defaulting to zero.
The optional artefact reward category supplies physical non-quest artefacts;
explicit quantity mode defaults to four when enabled. The Full Story preset
enables it. See [regional story balance](regional-story-balance.md) for container
selection, delivery limits and native acceptance still required.
Counts rotate deterministically across that category's published reward IDs.
Existing native reputation, skill, carry and finite stash/container caps remain;
additional receipts do not invent extra levels or new native containers.

The local generator supplies a suggested 0–50 slider and a numeric entry without
that suggested upper bound. A finite seed still has finite checks and a 4000
receipt/history bound. Generation rejects impossible requests instead of silently
trimming useful rewards or permissions. Counts are not literally unbounded.

## Conditional artefacts

With the new content contract, generic artefact checks use a base of at most 40.
Numbers 1–20 use detector and regional source access. Numbers 21–40 also require
melter/tool use, plus artefact recipe access in fresh regional contracts. A
configurable extra ceiling defaults to 60. Only a 40-type base
with melter enabled can add 41–60, and only enough checks to fit non-filler demand.
The resolver runs before region creation, accounting for exclusions, gifts and
start-inventory-from-pool. The resolved count enters slot data, configuration digest
and the native manifest. User-supplied derived counts are recomputed at generation.
Filler pressure alone never adds checks. Reducing the base quota below 40 disables
extra allocation; quantities that still do not fit produce a clear error.
Settings previews estimate this allocation before seeded starting gifts and common
AP options; actual generated reports are authoritative.

## Step calculator

Every optional actual-seed preview includes ordinary AP logical spheres and paced
steps. Paced steps complete all newly reachable checks, but take at most one tier
per knife, armour, repair-grade, rank, firearm-upgrade, armour-upgrade and tool-claim
chain (or fresh tool-use capability). Fresh equipment-class and generic-tool
receipts also advance at most one tier per chain per step; deferred copies are
listed in spoiler reports. Enemy-kill totals form a numeric chain per GAMMA slot:
if 10 enemies is completed in step one, 25 is considered from step two, then 50
from step three and 100 from step four, subject to their existing access rules.
Custom totals use the same ascending order and other players have independent
chains. This models one milestone per step, not a fixed number of kills per step.
Rewards arrive at the end of the step. Ordinary local goal events settle
between steps. This does not alter access rules, fill or actual game callbacks.
It models a slower playthrough, not measured minutes or a guarantee of difficulty.

Generate with a preview enabled and extract its _gamma_preview.json from the ZIP.
The local page's actual-seed calculator opens it without changing any session.
A summary shows counts; placement-spoiler mode also shows check/reward/recipient
lists at each step. All report strings are rendered as text, never HTML.
Ten filled seeds are regression-tested for completion, complete check coverage
and the one-tier limit. Native playtime and gameplay acceptance remain not run.
