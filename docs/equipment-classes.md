# Equipment classes

Fresh generators use `equipment_class_progression: 1`. Enable equipment rewards
to gate use by class, rather than by one binary firearm or outfit permission.
Inventory ownership remains unrestricted. The four starting-class settings default
to 1 and accept 0 (no class permission) through their maximum.

| Setting | Cumulative tiers |
|---|---|
| `initial_firearm_class` | A, B, C, D, from native `repair_type` |
| `initial_outfit_class` | Novice, Light, Medium/Scientific, Heavy, Exoskeleton/Nosorog |
| `initial_helmet_class` | Light, Medium, Heavy, Exoskeleton |
| `initial_backpack_class` | Basic, Small, Small Military, Military, Tourist |

Each matching progressive reward adds one tier. All lower tiers remain usable.
Unknown gear in a recognized group requires that group's highest tier; unclassified
inventory remains untouched. The catalogue owns repair-type and backpack mappings.
An MP5 using the native pistol repair kit belongs to A even though its role is SMG.
Powered outfits are explicitly classified at the exoskeleton tier.

GAMMA's enabled "Helmets need armor repair kits" override assigns
`repair_type = outfit_novice` to `helm_bandana`, `helm_cloth_mask`,
`helm_rp_bala` and `helm_resp`. These are helmet items and use the Light helmet
permission (tier 1), including when that permission is granted at the start.
The shared repair-kit name does not make them outfits. Medium, Heavy,
Exoskeleton and unknown helmet repair types retain their existing requirements.

Only backpacks include a physical class item: the initial permitted backpack is
supplied if missing, and each reward supplies its matching backpack even when
optional permission supplies are off. Firearms, outfits and helmets are use
permissions; ordinary GAMMA acquisition still provides the physical gear.

Knife ownership and use are always permitted in this contract. A missing starter
knife is supplied. The old generic Melee permission is absent from fresh pools;
the four better-knife checks remain. Reaching a later knife, armour or firearm
repair grade also credits eligible skipped lower tiers. Weapon roles (shotgun,
rifle, sniper, machinegun) are separate facts, not a linear chain.

## Creation and checks

The native creation inventory and offer lists are filtered before their cells and
point costs are constructed. Locked clicks and an inconsistent final selection
are rejected before the native action. Faction/map/story restrictions continue
through the existing start wrapper. Post-spawn reconciliation covers native
default grants. Later earned inventory is never stripped by the initial plan.

`equipment_check_condition` defaults to 65, range 0–100 inclusive. This is item
condition, not the proportion of installed upgrade attachments. A small numerical
tolerance accepts an exact threshold after native floating-point rounding. Broken or invalid
items never count. Equipped armour, active weapon/knife tiers and newly observed
upgrade installations use this threshold. Weapon roles, firearm repair classes,
armour tiers and knife tiers do not require Basic, Advanced or Expert tools to
earn their checks. For Class D only, regional AP placement logic and its PDA
projection require Expert Tools when tool rewards are enabled. This conservative
placement assumption never vetoes actual use of a qualifying Class D firearm;
Class A–C placement remains tool-free. Starting, bought or looted equipment can
already qualify without repair. Class permissions, condition and independent regional readiness
requirements still apply. Attachment installation totals retain the existing
conservative Expert-tool requirement because they observe a new upgrade action.

GAMMA's "Guns Have No Condition" add-on forces firearm engine condition to 83%,
so class-based sessions use the arithmetic mean of the weapon's required native
part conditions instead. The native `con_parts_list` and `parent_section` identify
the parts; the weapon body's saved condition and unrelated entries are excluded.
A native missing-part value of -1 contributes zero. Missing/unreadable or malformed
part data blocks a new check until valid data is available, without falling back
to the forced 83%. AP only reads existing part data; it never initializes or
rerolls parts. Weapons without a part system, legacy binary-permission sessions,
outfits, helmets and knives retain native item condition. The configured threshold
and its inclusive boundary still apply. Previously earned checks remain complete.

GAMMA's novice and trenchcoat outfits use `outfit_novice` and are permitted by
starting outfit tier 1. Outfit Light is tier 2; helmet Light is tier 1. Condition
requirements for earning equipment checks do not restrict carrying or equipping
an otherwise permitted class.

Fresh `progressive_tool_receipts: 1` replaces named Basic/Advanced/Expert rewards
with three identical Progressive Tools receipts. They unlock and supply Basic,
then Advanced, then Expert. Specialist kits retain their separate permissions.
The general Tools equipment lock is redundant in this contract and is retired.

The world derives class levels from starting settings and item counts; the game
derives them from the same settings and applied receipt history. No second saved
permission ledger exists. The tracker displays current class levels. Paced seed
analysis applies at most one reward per progressive class/tool chain per step;
logical AP spheres retain ordinary simultaneous collection.

## Compatibility and verification

Published IDs are retained. New class rewards use new item IDs 28053001–28053004.
Old configurations omit the new fields, default to zero and retain their digest,
binary gear permissions and named-tool behaviour. Existing sessions are not
upgraded in place. Initial free supplies use the central loadout plan; backpack
rewards use existing ordered delivery plans. Definite creation failure retries;
uncertain creation blocks automatic replay. Spawning and saving are not atomic.

Native acceptance is pending: creation at all four zero/default/max settings,
point accounting, equip/use guards, backpack grant/reload, knife availability,
condition boundaries and skipped-tier credit. Mocked engine tests establish adapter
behaviour only. No installed files, current session or private panel are changed
by this source work.
