# Step 12: equipment use and installed upgrades

Stack base: task PR #15. Four independent categories add twenty finite checks:
four armour tiers (28052701–28052704), six firearm classes (28052711–28052716),
four improved knife tiers (28052721–28052724), and 1/3/5 installed-upgrade
milestones for firearms and armour (28052731–28052736).

Armour uses the actual outfit in slot 7 with condition above zero. The catalogue
maps light, medium/scientific and heavy kinds to tiers 1–3, and explicitly lists
27 exoskeleton/Nosorog sections as tier 4. Weight, price, disguise and displayed
damage numbers do not determine a tier. Equipping a higher tier awards the
reached lower thresholds too; downgrading cannot remove or repeat saved checks.
The classification is a published project progression scale, not a claim that
every scientific suit has identical protection to every medium suit.

Firearms and knives must be the active, usable item, rather than merely present
in inventory. Firearm milestones are pistol, shotgun, SMG, rifle, sniper and
machine gun. These are parallel class milestones, not a claim that one class is
universally stronger. Engine item kinds handle ordinary variants, with 68 explicit
machine-gun sections overriding the generic rifle kind. The five baseline knives
and three axes have an explicit tier mapping; tiers 2–5 are the improved-knife
milestones and preserve a high-water mark. Unknown equipment is not guessed into
a class. The catalogue contains the mappings and exceptions.

Upgrade checks observe `iterate_installed_upgrades`, the same actual installed
list used by Anomaly's item utilities. A new owned item's list becomes its
baseline; pre-upgraded loot does not award installations. Later additions count
up to five each for firearms and armour/helmets. Repairs, prices, UI selections,
failed installation attempts and reappearing known upgrade IDs do not increment
the counter. Ownership/box callbacks establish baselines without replacing an
existing baseline during an inventory refresh. Polling catches successful changes
and handles at most eight eligible items per poll; completed groups need no further
inspection. Baselines are pruned when items leave the owned inventory and cleared
when both counters finish. Counters, cursor and plain-data baselines are saved and
deep-copied by the single AP state owner. No engine objects are serialized.

The inspected UI calls `install_upgrade` and then refreshes its display; the add-on
verifies the item's installed list. Payment/effect callbacks alone do not prove
success. Active-item, outfit-slot and
installed-upgrade APIs were checked against the pinned sources. Acquisition before
the first observation establishes a baseline, so an installation that happens
before either ownership observation or a poll can be missed. Gear modified outside
the actor inventory is baselined on reacquisition. Engine identity reuse with an
identical ID/name between observations is a remaining lifecycle boundary, not a
claim of an independent item UUID. Invalid/unavailable upgrade data is reported
without incrementing progress and can be retried.

The full verifier passes 419 covered tests and two real AP server cases, with
100% measured owned Python lines/branches and Lua executable lines. Coverage
includes active/worn/zero-condition gear, each firearm/knife mapping, high-water
marks, preinstalled loot, successful additions, repairs, repeated callbacks,
reacquisition, save copies, bounded polling, API failures and exact standalone
category generation. Lua branch coverage is not measured. Actual engine timing,
installed outfit classifications and upgrade-menu interactions are **not run**,
reserved for the user's post-merge acceptance. No game launch or deployment.
