# Step 09: combat checks

Stack base: settlement PR #12. Three independent options enable first mutant
species kills (25 checks), first stalker faction kills (13 checks), and a finite
list of cumulative kill milestones. Each list contains 1–20 unique increasing
thresholds, from 1 to 10,000. A threshold's location ID is 28100000 plus its count;
changing list order or adding a threshold cannot rename another check. Only the
selected thresholds become seed locations. The complete AP data package reserves
the range without generating ten thousand checks in a seed.

Species use the inspected creature class/kind identifiers, with explicit section
families for Borya, Bibliotekar and the jumping pseudogiant. Poltergeist, pyrogeist
and pseudogeist are distinct. Psy-dog phantoms, generic hallucinations and crows
are excluded from both first kills and totals. Factions use actual character
community, with military/Sin story-NPC aliases mapped to their parent factions.
Disguise and player faction do not rewrite the victim's recorded community.

Credit requires an actual dead victim and the player actor as killer. Companion,
other NPC, environmental, missing-killer and self deaths are excluded. The base
monster death routine emits a hit callback marked `from_death_callback` before
releasing poltergeists; normal monster deaths additionally emit the death callback.
The adapter observes that marker and the regular callback, deduplicating by victim
ID/name. An alive net-spawn clears the identity marker, allowing recycled engine
IDs to count for a new life while dead-object reloads remain deduplicated. This
depends on the inspected binder's lifecycle; mod-driven resurrection without a
net-spawn is not a tested compatibility claim.

Counters and the deduplication set are saved together under the existing AP state
owner. Totals stop at the largest configured threshold, bounding history to at
most 10,000 identities. First-type checks still work after saturation and when
total counting is disabled. Loading an older save restores its local count;
server-confirmed checks remain monotonic. There is no claim that replaying game
history across saves is a globally unique lifetime kill ledger.

Global combat locations currently assume ordinary access to the game's activities;
they do not encode mutant habitat, faction spawn or future key restrictions.
Those assumptions must be tightened with the gate/progression branches. The
current development goal remains the independent three-map tour. Pool sizing now
also handles a one-check seed without overflowing it with three starter rewards.

Verification passes 388 covered tests and two real AP server cases, with 100%
measured owned Python lines/branches and Lua executable lines. Tests cover every
species mapping and faction, death/hit duplicates, actor attribution, phantom
exclusion, copied saves, older-save rollback, recycled IDs, counter saturation,
custom thresholds, disabled categories and one-location pool sizing. Lua branch
coverage is not measured. Actual engine kill attribution and poltergeist timing
are **not run**, reserved for the user's post-merge acceptance. No game launch,
deployment or protected-root modification was performed.
