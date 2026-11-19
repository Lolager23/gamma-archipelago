# Step 06: restricted starting loadouts

Stack base: category-options PR #9. Equipment options accept normal or absent;
AP-locked mode remains unavailable until the starting-gear unlock branch.
Detector, PDA, firearms, melee, outfit, helmet, backpack, tools and utilities are
independent. No Starting Weapons additionally omits explosives. Ammunition,
medicine, food and money use integer percentages from zero to one hundred.

The adapter filters the character-creation loadout before Anomaly grants it,
using item classes and kinds rather than a faction-specific item list. After the
base grant finishes, a saved one-time plan adjusts quantities and removes any
remaining omitted items. Work is bounded to 32 inventory actions per poll. The
plan stores original item identities and target quantities, so retries neither
halve supplies again nor remove later acquisitions. Quest items with unknown
equipment classifications are preserved. AP receipts wait for initialization.

Restricted seeds require a fresh character and the matching companion running
before character creation. Attaching such a seed to an existing character is
refused. Unrestricted configured seeds can attach without an inventory sweep.
Ordinary load/reload preserves earned equipment and the initialization marker.
This is an initial omission, not a permanent ban on buying or finding equipment.
When the initial PDA is absent, reward notices remain queued until a PDA exists.

Newly generated seeds use slot schema 2 and incoming snapshot version 2. The
snapshot names a configuration digest; a separately validated, bounded data-only
configuration file must match both session and digest before inventory mutation.
Version 1 pilot seeds remain supported and never modify starting inventory.
Old clients must not be used with schema 2 seeds. Published pilot item and
location IDs and the saved receipt format are unchanged.

Source inspection covered the active GAMMA character-creation override, its
automatic ammunition grant, startup callback order and inventory APIs. Engine
timing, faction/custom-loadout variants and visible no-PDA behaviour remain
**not run** for the user's post-merge verification. No game was launched for this
step. Mocked-engine tests cover retries, save/load, missing configuration, reused
item IDs and subsequent earned equipment. Verification passes 359 covered tests
and two real AP server tests, with 100% measured owned Python line/branch and Lua
executable-line coverage. Lua branch coverage is not measured.

Parser regression assertions now require an actual Lua error tuple. Indexing a
Lua table at zero also yields nil, so that old assertion could accept a parsed
table accidentally. Malformed configuration and notice/confirmed-check tests
now distinguish rejected input from successfully parsed tables.
