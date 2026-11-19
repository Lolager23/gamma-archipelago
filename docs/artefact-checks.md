# Step 10: artefact acquisition checks

Stack base: combat PR #13. `checks_artefacts` adds 66 finite first-acquisition
checks, IDs 28052401–28052466. The catalogue lists every supported section and
its actual container aliases. Condition is not a type: degraded, improved or
repeatedly picked-up copies cannot produce another check for that type.

The roster is the intersection of actual artefact item definitions and the active
GAMMA anomaly-zone spawn lists. This avoids treating similarly named backpack
attachments, empty containers, inherited configuration bases or obsolete artefacts
as obtainable types. Legacy SoC-only definitions, anomalous bread, quest/task-only
special artefacts such as Lucifer, Lost Soul and Prometheus, and other definitions
outside that spawn roster are not generated as checks in this increment. Supporting
their separate acquisition routes remains explicit follow-up work, rather than
advertising them as reachable because their section exists. The active PBA/GAMMA
item definitions, container sections, artefact spawn settings and ownership
callbacks were inspected; no game assets were copied into the repository.

The ownership callback accepts world pickup, trade or crafting results that enter
the actor's inventory through that callback. The box-transfer callback also counts.
Saved provenance records `ownership` or `container`; the ownership event does not
identify whether its source was pickup, trade or crafting, so the add-on does not
invent that detail. It does not scan existing inventory to manufacture an event.
An existing character's old item counts only if a qualifying acquisition occurs.
The stored check is monotonic and aliases/condition changes do not farm it.

Callbacks fired synchronously during AP reward creation are suppressed. Direct AP
rewards currently contain no eligible artefacts, enforced by a catalogue regression;
therefore delayed creation callbacks cannot feed eligible artefacts back into checks.
Later stash/reward branches must preserve that restriction or add persistent item
provenance before introducing any eligible artefact as AP loot. The synchronous
guard alone is not claimed to identify delayed engine callbacks. Creation exceptions
clear the transient guard and leave the receipt pending for retry.

The current world assumes ordinary anomaly access; northern habitat/protection
constraints must be represented when AP access gates are introduced. Existing
pilot seeds and disabled categories emit no artefact checks. Confirmed checks can
survive older-save rollback independently of the physical inventory in that save.

Verification passes 395 covered tests plus two real AP server cases, with 100%
measured owned Python lines/branches and Lua executable lines. Tests cover every
type/alias, source validation, duplicate acquisitions, save copies, disabled and
legacy sessions, AP creation feedback, creation exceptions and pool generation.
Lua branches are not measured. Actual pickup/trade/crafting callback timing,
container behaviour and spawn availability are **not run**, reserved for the user's
post-merge verification. No game launch, deployment or protected-root modification.
