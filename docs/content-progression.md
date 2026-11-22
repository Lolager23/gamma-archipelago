# Practical content progression

New seeds use content_progression=1. Older snapshots omit the option and retain
legacy catalog selection and tool permissions. Existing IDs and save schema are
unchanged; new settings require a fresh seed and coordinated bundles.

## Weather and stories

Emission and Psi Storm checks are independently optional. Observation requires a
surface map and the shared active-world readiness gate, then the actual native
manager reporting an active event. These checks are excluded from early equipment
placements. They do not assert that the actor survived the entire event.

Living Legend, Mortal Sin and Operation Afterglow have independent check switches.
The latter arcs also have separate goals. The forced AP start enables native
story mode for any enabled story arc or story goal before character creation. Goal completion uses recorded native
completed-task callbacks, not early objective info flags. Their AP access chains
retain preceding story permissions. Brain Scorcher shutdown is Radar/X19
(bar_deactivate_radar_done); X18 supplies Dark Valley documents, while X16 is the
Yantar brain facility. The all-labs goal intentionally includes X18; Brain Scorcher
has no explicit X18 shutdown dependency.

## Tools, melter and equipment

Fresh progressive-tool seeds replace the three generic copies with Basic,
Advanced and Expert orange progression stashes. Each contains its physical kit
in a supported Cordon container. Applied receipts unlock the corresponding
permission; solver claim events also require reaching Cordon and prior tiers.
Advanced and Expert placements require progressively later reliable checks.
Only the calibrated psi stash grants psi protection; tool boxes cannot do so.
The Artefact Melter is a separate optional physical reward (itm_artefactskit).
Generic distinct artefacts above 20 require melter and tool-use access; without
that reward enabled these late checks cannot hold progression or useful items.

Weapon checks cover the existing role classes plus repair grades A/B/C/D, using
the active repair_type mapping. Heavy/exosuit and grade D AP checks wait for usable
psi protection, Red Forest and a northern region, or 2000 AP-earned goodwill with
one baseline-friendly trader faction. This changes check eligibility only;
equipping those items remains governed by ordinary equipment permissions.
Rank uses one faction's AP-granted goodwill as a proxy, and a repeatable task or
firearm earning route. Rank is not native faction goodwill or an XP grant.
AP reputation floors preserve earned neutral access; alliances and individual
NPC grudges remain native. Hostile-faction goodwill cannot substitute for friendly
trader access. The first 2500 RU Cordon contract can use the 5000 RU starting
allowance; other paid checks require a repeatable earning route.

Infinite stamina is opt-in and defaults off. On active-world updates it restores
only native actor power; health, radiation, hunger and thirst are untouched.

## Distinct artefact counts

The catalogue has 66 canonical types. The active anomaly-field model supports 60
ordinary field types; Atom, Compass, Death Lamp, Fountain, Monolith and Oasis Heart
are excluded from progression sources. Regional availability is the union of
canonical artefacts in the active artefact groups actually referenced by that
region's anomaly fields. Duplicate groups and contained-item aliases count once.
Cordon has 23 possible types, Garbage 31 and Red Forest 35. These are opportunities,
not simultaneous spawns or a promise to find every type in a fixed time.
Jellyfish (af_medusa), Sparkler (af_electra_sparkler) and Battery (af_dummy_battery)
are examples. Contained Jellyfish variants are still one type. Crystal
(af_cristall) is absent from the Cordon model but appears in other regional fields.

Source inspection used the effective Dev override index and pinned engine
7289a03f19a3cc712d9fc4cf6122345984c8c094. The engine exposes writable actor power;
GAMMA repair-kit naming and repair_type definitions establish grade A–D mapping.
This is source evidence. Native weather, story callbacks, physical kit retrieval,
late equipment eligibility and stamina acceptance remain not run for Owen.
