# Buyable Archipelago shop checks

`checks_shop_purchases` is an independent APWorld toggle, off by default. It adds
nine location checks: three contracts at each of Sidorovich, Barman and Sakharov.
Each trader charges 2,500, 7,500 and 15,000 RU: 25,000 RU per trader and 75,000 RU
for all nine. Prices are fixed service prices, independent of native stock prices.
The catalogue owns each contract's ID, name, description, trader and price.

The **AP shop** button sits at the bottom of the trader identity section, above
the supply-rank and money row. Its 18-unit height fits the supported header gap
from y=60 to y=80, leaving the rank visible and staying left of the money display.
It switches the NPC pane between native goods and three contract cards. Cards
show the official Archipelago icon, the actual check name/description, its price
and a Buy/Purchased/payment-review status. Long descriptions and scouted rewards
scroll within each card. Native goods, their prices and the player inventory
retain their normal delegates. Repair, loot, unsupported traders and disabled
seeds do not offer AP contracts. The page does not create resalable inventory
tokens or alter a trader's native stock.

Buying completes the named AP location. It does not promise a particular physical
reward or a reward for this player. With scouting enabled, known reward/recipient
metadata appears on the card; disabled scouting never reveals cached rewards.
The companion sends the configured check and receives its seeded reward through
the usual channels. Close trade to resume normal game-update delivery if the UI
pauses the world. The PDA lists these checks in their trader's region, and reward
announcements describe purchasing the contract.

## State, money and recovery

The coordinator revalidates session/configuration, receipt-history prefix and
server-confirmed checks before spending. The adapter checks the current visible
trade partner, the enabled catalogue offer, prior completion and the actor's
actual integer balance. It deducts exactly the listed price with the native
`give_money` API and verifies the resulting balance. Repeated clicks or a loaded
older save whose check is already server-confirmed do not charge again. Native
wallet changes update affordability without polling AP files every UI frame;
normal metadata refresh is bounded to 500 ms, with explicit action refreshes.

The central save owns a bounded `shop_payments` intent map, not a separate shop
state owner. A proven unpaid failure can retry. A proven debit marks the check
even if a subsequent native callback threw. An unexpected balance or unreadable
result retains an uncertain intent and blocks another debit pending manual review.
It does not automatically refund or manufacture a completion. Confirmed server
checks resolve obsolete intents. Old saves without this optional map load as
empty; malformed intents are refused before copying. There is no engine-wide
transaction or crash-proof exactly-once currency guarantee.

A failed outgoing file write retains the paid check in the game save and reports
that delivery will retry. It cannot undo the purchase or charge it again. Normal
check/receipt processing continues when the optional shop UI is unavailable.

## Generation and compatibility

Published IDs **28052921–28052929** are new. The earlier `checks_shops` option and
its IDs retain their original first-ordinary-purchase behaviour; buying an AP
contract is independent of that category. The new default zero is omitted from
the configuration digest and wire option records, preserving existing seed
identities, location sets and disabled-shop configurations for the previous add-on.
Enable the option in a **new seed**, upgrade world/client/add-on together, and
use a fresh Dev character for that seed. Existing bound characters are not reset
or silently attached to another seed. The current Brain Scorcher session stays
unchanged and does not acquire new locations retrospectively.

The existing missable service-check policy applies: exclude progression by default,
omit entirely, or explicitly allow progression. Availability of named NPCs and
earning currency through normal play are native assumptions, not solver-proven
income or spawn guarantees. Regional access rules still apply. Required
progression is budgeted before the reward pool is filled; default exclusions keep
required unlocks out of these purchases. Settings previews list individual prices
and the exact selected `shop_cost_ru`; income-grind time is not calibrated into
the playtime estimate. See `examples/shops/shop-purchases.yaml` for a small fresh-seed
configuration.

## Assets and acceptance

The coloured icon is the pinned Archipelago 0.6.8 `data/icon.png`, copyright Krista
Corkos and Christopher Wilson, under CC BY-NC 4.0. The source PNG and its SHA-256
are retained with attribution. A standard-library build tool converts it to a
64px RGBA DDS; all 4,096 pixels matched an independent Windows decoder/reduction.
The package includes its separate licence notice. No Anomaly/GAMMA art or scripts
are redistributed. See [licence review](licence-review.md).

Source probes inspected the active GAMMA `UIInventory` class and its `_16` layout
(the base XML includes that layout), `UICellContainer`, native wallet use and
pinned Monolith texture-descriptor discovery. The AP page adds owned controls
and captures `TMode_Init`, `Reset` and `Update` delegates; it replaces no base file.
Regression, coverage, generation/server and current-head CI results are on the PR.
Model/asset previews are not in-game captures.

Native acceptance remains **not run**, for Owen:

1. Generate with the new toggle on and start a fresh Dev character, retaining the
   existing session/saves separately. Confirm the disabled option leaves traders normal.
2. Earn enough money and buy each contract at each of the three traders. Verify
   the exact expense, named check, AP reward/recipient, Purchased status and icon.
3. Check insufficient funds, repeated interaction, save/reload, offline delivery,
   reconnect and older-save/server-confirmed recovery without another charge.
4. Check normal goods/sales, repair and loot modes, another NPC, all supported
   aspect ratios, long labels/scrolling and leaving/reopening the trader.
5. Check scouting off versus on; only known metadata should reveal a reward.
