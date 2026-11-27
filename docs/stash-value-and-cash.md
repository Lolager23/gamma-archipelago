# AP stash value and cash

Unclaimed AP packages keep their original, frozen contents and receive a varied
bonus with at least the same nominal item value. This targets twice the loot value,
not two copies of every item. Unique progression items remain single. Every newly
claimed AP package additionally pays 5,000 RU; cash is separate from the value
target. Already-claimed old packages are not reopened or paid retroactively.

The adapter freezes positive/zero native `cost` values for the approved original
sections and their tier/calibre supply pool. It preserves the original action
prefix, including any already-created object identities. A local receipt/session
PRNG selects additional supplies within the remaining value budget, with at most
64 bonus objects and less than one cheapest-item overshoot. Original randomized
contents/calibre remain unchanged. A zero-price quest item instead gets at least
5,000 RU of ordinary bonus supplies, while the quest item stays single.

The optional versioned `loot_value` price snapshot lives in the existing stash
record and regenerates its exact approved section plan during save validation.
Later price changes, reopening and save/load never reroll it. Unsupported/malformed
prices or an impossible bounded budget leave the reward pending with an error.
Nominal prices are a tuning estimate, not a guarantee of twice the resale proceeds:
native condition, charges, trader relationships and pricing still apply.

The original `loot_version` remains intact for baseline/fixed and random version-1
plans. Old unclaimed records receive the bonus before opening/continued creation;
their existing action prefix is preserved. Other items already in that physical
world/quest stash are not valued, removed, duplicated or claimed by AP.

The first actual AP-item acquisition claims an ordinary package; protected direct
inventory delivery claims after its full saved plan completes. Its saved 5,000 RU
cash target is absolute and confirmed through the native money getter. Failed
setters retry the same target; successful claims never repay after spending,
reopening or normal save/load. At the engine balance cap the complete payout waits
until sufficient room exists. Native mutation and saving are not an atomic
exactly-once transaction; retain the pre-update backup and do not downgrade a new
plan without restoring its matching save/bundle.

AP and native stash markers remain separate, but containers are shared rather than
reserved. Native reward/quest content can coexist. Another mod deleting a container
or removing already-created AP loot is not automatically repaired by respawning it.
Multiple AP packages at one box retain individual plans and cash entitlements.
Creation budgets remain 64 objects per opening and eight per timed update.

No AP item/location ID, server seed, receipt order or configuration digest changes.
Native GAMMA acceptance remains for Owen and Mini; no agent launches/loads the game.
