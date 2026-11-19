# Step 38: bounded convenience rewards

Stacks on supply packages PR #46. APWorld `rewards_convenience` is off by default.
It adds up to three useful `Carry Capacity +5 kg` items, capped at a total +15 kg.
The pool reserves required progression first and includes as many of those three
copies as reliable remaining checks can hold. A configuration with no eligible
space refuses generation. These rewards are optional usefulness, not required
access to a goal. The PDA shows the saved AP carry permission and its cap.

The active development profile's `weight.script` winner is GAMMA Arti Recipes
Overhaul. Its `add_weight(key, amount, force)` and `remove_weight(key)` functions
support named additive modifiers and recalculate both carry and walk limits. The
add-on uses only `gamma_archipelago_carry`, leaving the base and other named
modifiers owned by that API. The supported source was inspected directly. This
increment's convenience reward is carry capacity; other native convenience APIs
need their own explicit adapter before becoming new reward effects.

The desired bonus derives from central applied receipts. A bounded adapter cache
avoids repeated setters, and the named value is replaced rather than accumulated.
Save rollback, a new actor, disabled configuration or refused save reconciles the
owned key on the next bounded update. A failure after a possible keyed mutation
can retry idempotently; it does not acknowledge the receipt. Missing or refusing
weight APIs report a pending reward. No separate mutable carry progression is
saved, and no item is spawned.

One new item ID is added. Existing IDs, save/receipt formats and default digests
retain their meaning. Non-default use requires a new generated seed and matching
world/client/add-on bundle. The later pool-budget increment handles common AP
starting inventory and provides richer counts in generation previews.

The complete verifier passed: 944 covered tests, 39 untraced generator/server
tests and five Node tests (988 total), including 50 filled convenience/zone-key
seeds. Owned Python runtime modules reached 100% measured line/branch coverage;
Lua reached 100% measured executable lines. Lua branch coverage is not measured.

Native verification is **not run**, reserved for Owen: actual weight and walk
limits, other modifiers, option changes, actor/load transitions and rollback.
No game launch, deployment, installed-game write or developer-panel change is
included.
