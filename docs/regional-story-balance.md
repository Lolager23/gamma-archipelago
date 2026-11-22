# Regional diversity, story readiness and artefact rewards

Fresh seeds use `regional_progression: 1`. Omitted older configurations use zero,
preserving their digests and declared access rules. This changes future generation;
it does not repair an existing archive or switch a running session.

## Declared progression requirements

| Check or logical event | Additional requirements |
|---|---|
| Turn Off Brain Scorcher; shutdown event | Advanced tools, Medium/Scientific outfit permission, Class C firearm permission |
| Later Living Legend steps before Path Pripyat | Retain the Scorcher readiness requirements |
| Path Pripyat and subsequent story steps/goals | Expert tools, Heavy outfit permission, Class D firearm permission |
| Fire Machinegun; Exoskeleton/Nosorog check | Scorcher disabled, Red Forest reachable and another northern region reachable |
| Distinct artefacts 21–40, and optional overflow | Artefact recipe permission as well as the existing melter and detector requirements |

The northern-region set includes Limansk. AP goodwill cannot replace the new
Scorcher/Red Forest requirement for machinegun or exoskeleton checks. Their own
class and repair-tool requirements also apply. World events and terminal goals use
the same story definitions, preventing a goal from silently bypassing Path Pripyat.
Categories switched off impose no AP permission requirement for that category;
ordinary GAMMA acquisition and native requirements remain. These are conservative
solver assumptions about usable equipment, not an inventory simulation or a new
native prohibition on completing a difficult quest early. Actual quest completion
still counts. Equipment checks themselves inspect the real item and condition.

## Generic mutant checks

The starting region contributes at most five distinct supported mutant types.
Each additional reachable region contributes at most two, and only when the
catalogue documents distinct source types there. Visiting a region repeatedly,
adding a region without a supported source, or killing repeated copies of one
type adds no diversity. The solver uses maximum matching between source types and
regional capacity: one type cannot occupy several regions, and a common type can
be reassigned to preserve a limited source's only region. Exclusions and the
existing progression ceiling/filler tail still apply. Named-type mode is unchanged.

This is an upper bound for logical availability, not a spawn guarantee or a runtime
limit on credited kills. Finding an unusual mutant early still counts. The PDA
uses the same capacity calculation as the APWorld. Starting-region capacity follows
the resolved AP start; settings-only Random previews remain conservative at Cordon.

## Artefact rewards

`rewards_artefacts` adds useful physical rewards from the 60 supported non-quest
types. The six unsupported/quest-only discovery types are excluded. Explicit
quantity mode defaults to four rewards when enabled; `artefact_rewards` accepts
0–4000 subject to pool and receipt capacity. Its numeric entry may exceed the
slider's suggested range. Counts cycle through the named roster, and AP randomizes
their check placements. Legacy weighted mode can select from the enabled roster.
The Full Story preset enables the category; the bare AP option defaults off.

Rewards use a documented lead-container variant when available. Non-container
variants are the roster's ordinary supported sections. The native creation API
receives `cond=1`; the existing ordered delivery plan handles failure, uncertain
creation and save/load. Optional permission supplies do not disable artefact rewards.
No detector or recipe permission is granted implicitly. The existing applying-
reward guard suppresses synchronous acquisition callbacks; asynchronous native
pickup behaviour remains an in-game acceptance item. The solver never relies on
receiving these useful rewards to satisfy discovery quotas.

## How Archipelago chooses placements

Our world declares regions, connections, item-count requirements and local logical
events. Archipelago's restrictive fill queries these rules while placing rewards.
For a unique key, a proposed location must be reachable without already having that
key. Progressive rewards use counts: removing the final Class C or Advanced Tools
copy makes Scorcher unavailable, so that necessary copy cannot depend on Scorcher.
Early opening reservations and explicit excluded checks remain deliberate exceptions
to otherwise random placement. Keys are not assigned to matching map checks.

New 04 exposed a missing declared native gate. The active Free Stalker northern psi
field needs both the X16 Miracle Machine and X19 Brain Scorcher disabled. The
declared Living Legend Scorcher route includes Agroprom and its underground:

```text
Agroprom key -> Agroprom -> Agroprom Underground -> Scorcher -> Generators
```

With that route declared, the Agroprom key cannot be justified at Generators using
its own future unlock. A northern key may still appear early; its destination
remains blocked until its real access requirements are met. Logical spheres collect
all accessible rewards together. The separate paced calculator limits progressive
class/tool rewards to one tier per chain per step and lists deferred receipts.
Neither report measures travel time, encounter luck or native acceptance.

Primary reference: [Archipelago 0.6.8 World API](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/docs/world%20api.md).
Native source hashes and archived New 04 evidence are retained privately. No game
assets or private session files are included in Git.

Regenerating New 04's input seed with the corrected rules placed its Agroprom key
at Sidorovich's Cordon Expedition Contract. Even collecting every other network
reward leaves both Scorcher and Generators unavailable without the Agroprom key.
That fresh archive is logically beatable with every check reachable: 22 initial
checks, 11 logical spheres and 12 paced steps, with Living Legend at paced step 8.
The original archive, its analysis and the current playable session are unchanged.
This demonstrates the declared dependency and fresh fill, not native acceptance.

## Acceptance still needed

Owen should verify real mutant availability across several regions, Scorcher and
Path Pripyat readiness in the tracker, machinegun/exoskeleton check timing, recipe
and melter use, contained artefact condition/radiation and asynchronous discovery
callbacks. These checks require GAMMA. Agents do not launch the game. Source work
changes no installed files, developer panel, current session or normal installation.
