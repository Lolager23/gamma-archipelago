# Ordinary shop purchase detection

The initial adapter only listened for the engine `actor_on_trade(item, sold,
money)` event and resolved the NPC using `mob_trade.GetTalkingNpc()`. GAMMA's
custom inventory instead purchases through `UIInventory:TMode_Buy` and transfers
items and money directly. The installed Monolith `callbacks_gameobject.script`
wraps this route and emits `actor_on_item_buy(item, price, trader)`. AP did not
listen to that event, so a real purchase could leave its ordinary shop check open.

The game coordinator now registers this existing native purchase callback. It
passes the explicit trader to the same finite service-check adapter. That avoids
requiring the shopkeeper to remain in the engine's talking state. The legacy
trade callback remains supported and shares the same monotonic saved check.
There is no new UI wrapper, purchase transaction, pending queue or state owner.

The native item-price calculation can return a fraction. Valid prices with a
positive whole-ruble part are rounded down before the existing integer-price
validation. Zero, sub-ruble, non-numeric, non-finite and oversized values cannot
complete a check. The session/category/location must be enabled and the save must
not be refused. Unknown traders, sales and dedicated AP contracts do not count.

## Inspected boundary and acceptance

Read-only inspection covered the installed `callbacks_gameobject.script` purchase
and sell wrappers; GAMMA UI `TMode_Buy`, `TMode_Sell` and `On_Item_Exchange`; and
Anomaly `utils_item.get_item_cost` / `mob_trade.GetTalkingNpc`. The custom UI checks
affordability before exchanging items. Its native purchase event is an accepted
purchase observation; AP does not take ownership of payment, transfer or rollback.
This is the already-installed callback contract, not an engine baseline upgrade.
Native transaction failures after an event remain an engine boundary, not an
atomic AP transaction guarantee.

Regression tests exercise the registered game callback without the legacy trade
event or talking-NPC helper, all three traders, fractional prices, repeated and
overlapping callbacks, refused/unconfigured state, unknown/unsupported partners,
free/rejected transactions, sales, AP contract separation and save/load.

Published IDs, seed configuration, saved receipts and schema are unchanged.
Source work does not deploy to either game installation, launch GAMMA or change
the private developer panel. In-game acceptance remains Owen's: buy normal stock
from each supported trader in a fresh seed, including ammunition/multi-use items,
then check repeats, sales, unaffordable/free transfers and save/load.

Separately, at Owen's explicit request, the active server's three ordinary shop
locations were completed for Owen and Mini using native per-location admin
commands after verified server-save backups. The paid AP contract locations,
seed, existing checks and normal installation were preserved. Private recovery
evidence and backups remain outside Git.
