# AP starts, purchases and transition safety

Newly generated worlds require an AP start. The APWorld `starting_faction` supports
only `free_stalkers`; `starting_location` selects `rookie_village`, `hidden_base`,
`lodging_house`, or `random_location`. The native Free Stalker roster supplies the
coordinates. Random is resolved once by the seeded world RNG before region creation
or item placement, then the selected preset is bound into slot configuration.
The main-menu start controls and final start action use that choice. Without the
matching companion configuration, starting a character is refused with a warning.
Living Legend/Strelok starts enable Story Mode and disable Warfare.

The menu uses captured native delegates, not a replacement faction-selection
script. The starting region is also the AP graph root and a permanently available
zone. Cordon remains ungated because it has no published key. The starting zone's
redundant key is omitted from required placement; exploration routing and protected
opening candidates use the chosen region. Checks, rewards and published IDs retain
their meanings. Unsupported/insufficient configurations reject generation instead
of placing an unlock behind its own requirement.
With exclusive psi stashes, the route must reach Cordon as well as Yantar before
entering psi-gated maps. A real mixed-game Rostok-start generation regression
reproduced the circular route through Radar that this additional rule prevents.

`ap_start` is an enforced new-world option, with only the required value exposed
by APWorld. Legacy slots missing these settings retain zero defaults, old digest
and wire bytes. Existing bound saves are not repositioned or assigned to another
seed. Use a new seed and fresh character for the new starting settings. Settings-only
workbench previews/exports normalize the required AP-start flag for new generation;
this does not rewrite the configuration of a running server or existing save.
Settings-only
previews do not roll Random; their conservative budget uses Cordon, and the real
generator validates the resolved start. Native availability/friendliness is still
a game assumption; only the three active Free Stalker presets are supported.

The purchase guard inspects the complete NPC trade basket before native transfers
or money changes. Any AP-locked equipment/psi-protection item, or a disappeared
item, refuses the whole basket and shows a warning. Removing the blocked item lets
the ordinary transaction proceed. Unrestricted items, sales and unlocked equipment
retain the native methods and return values. No post-charge refund is attempted.

Extra Level Transitions are blocked before their proximity dialog and before
travel side effects. Ordinary native changers are disabled while locked. Proximity
and denied travel show an Area Key warning, throttled to five seconds.

The pinned engine's silent `CLevelChanger::feel_touch_new` path sends its packet
without consulting the enabled flag. Its pre-load hook is void, so Lua cannot
reliably cancel an already accepted native load. That fallback now prefers the
real inverse transition's arrival coordinates (Garbage -> Cordon for a denied
Cordon -> Garbage attempt). It validates that point against all relevant volumes,
not only objects already registered in `db.storage`.

A bounded ALife scan reads native changer geometry/destination packets, including
unregistered changers. Conservative horizontal bounds with clearance cover sphere
and rotated-box shapes, slopes and overlapping zones. Extra-transition configured
positions/radii are included before their client objects register. Unsafe inverse
arrivals are rejected; the graph fallback must also clear those bounds. This avoids
choosing a north-side graph point still inside the western Cordon transition.
If the engine exposes no safe recovery point, the existing explicit failure remains;
neither the denied target nor an unvalidated trigger point is forwarded. This rare
scan runs on accepted denial, not every update. Native disabling does not control
silent changers; a recovery load may still be needed for an already accepted packet.

Primary baselines: active GAMMA faction menu/starting-location plugin and
`UIInventory:TMode_Buy`; extracted `bind_level_changer`/`utils_stpk`; pinned
[Monolith changer implementation](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrGame/level_changer.cpp).
No native game scripts or spawn assets are redistributed.

Native acceptance is **not run**, reserved for Owen:

1. Generate each fixed start and Random, open New Game, confirm Free Stalkers and
   the seeded location, then spawn with matching AP region/key availability.
2. Buy locked equipment alone and in a mixed basket: warning, no debit, no transfer.
   Unlock it and retry; check ordinary purchases, sales and missing basket entries.
3. Approach western Cordon -> Garbage from both south and north, repeatedly and
   after save/reload. Denied travel must warn and recover outside all triggers;
   receiving the Garbage key must restore ordinary and extra-route travel.
4. Check a second native/silent/extra route, old saves, native loadout restrictions,
   private developer panel and normal-game isolation.
