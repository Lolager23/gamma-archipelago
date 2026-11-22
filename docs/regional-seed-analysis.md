# Ten random Full Story generation samples

Ten independent 64-bit seed numbers were drawn once from the operating system's
random source. None were filtered or rerolled. Each ran the actual pinned AP 0.6.8
generator and produced an archive; its filled world was then traversed through
logical spheres. No host, companion, game save or active session was used.

All samples have **273 network checks**, **235 progression-eligible checks** and
**32 zone keys**. The other 38 checks are filler-only under the default missable
policy and unsupported-source protection. All ten generated successfully, were
logically beatable and reached every network check in the model. This is not
native encounter or completion-time evidence; unsupported optional opportunities
remain uncertain as described in [regional logic](regional-activity-logic.md).

The following columns count **zone keys**, not the total number of checks.
Combat combines mutant/faction first kills and kill milestones. Tasks/story
combines quest types, side-task milestones and story checks. Equipment/rank
combines worn/active tiers, upgrades and rank. There is no forced category quota.

| Sample | Maps | Settlements | Combat | Artefacts | Tasks/story | Equipment/rank | Last-key sphere |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 6 | 5 | 4 | 6 | 7 | 4 | 13 |
| 2 | 8 | 3 | 4 | 10 | 5 | 2 | 16 |
| 3 | 5 | 4 | 5 | 9 | 3 | 6 | 15 |
| 4 | 5 | 1 | 4 | 7 | 10 | 5 | 12 |
| 5 | 3 | 5 | 5 | 8 | 5 | 6 | 11 |
| 6 | 8 | 2 | 2 | 9 | 7 | 4 | 16 |
| 7 | 7 | 8 | 2 | 7 | 4 | 4 | 14 |
| 8 | 2 | 3 | 7 | 11 | 6 | 3 | 12 |
| 9 | 5 | 2 | 5 | 13 | 3 | 4 | 12 |
| 10 | 6 | 2 | 3 | 16 | 3 | 2 | 10 |
| **Mean** | **5.5** | **3.5** | **4.1** | **9.6** | **5.3** | **4.0** | — |

Every sample starts with nine logically reachable checks, five of which are
progression-eligible map/settlement/baseline-rank checks; the other four are optional shops.
One earned early permission is requested when necessary to open activities;
the full opening safeguard is described in the regional logic document. These
results use that final safeguard and the same original ten random seed numbers.
A sphere is a batch of checks reachable
from previously collected logical rewards, not a time estimate or a required
player itinerary. Actual encounter order can differ and native testing is not run.

## Reproduction seeds

These historical samples use named-type discoveries. To reproduce them after the
generic-default change, explicitly set `mutant_discovery_mode`,
`faction_discovery_mode` and `artefact_discovery_mode` to `per_type` (`0`) on the
`full_story` preset and disable `settlement_reputation_logic` (`0`) to retain the
historical settlement policy. Generate
without custom plando, early-item changes or spoilers, using
each seed below. Run the full verifier separately; these ten
samples supplement its deterministic matrices and server tests.

| Sample | Seed |
|---|---:|
| 1 | `1405700000417133490` |
| 2 | `16836709736012065217` |
| 3 | `15527498682095221728` |
| 4 | `3733791958397871077` |
| 5 | `10992578764514172978` |
| 6 | `284246225143801172` |
| 7 | `12432729445866381699` |
| 8 | `7299862164674971722` |
| 9 | `13759569452100432405` |
| 10 | `8323423946362295497` |

Compared with the prior active seed's 20 map-arrival keys and 12 settlement keys,
these samples use 2–8 map arrivals, with the remaining keys spread across the
newly eligible activities. The sample mean is descriptive, not a probability
promise or a playtime/balance acceptance claim. The active seed was not changed.

## Reward pools

Counts come from the actual generated archive item flags. Each check holds one
network reward; the 32 zone keys above are part of progression, not extra rewards.

| Sample | Progression | Useful | Filler | Total |
|---|---:|---:|---:|---:|
| 1 | 55 | 58 | 160 | 273 |
| 2 | 55 | 56 | 162 | 273 |
| 3 | 55 | 57 | 161 | 273 |
| 4 | 55 | 55 | 163 | 273 |
| 5 | 55 | 62 | 156 | 273 |
| 6 | 55 | 52 | 166 | 273 |
| 7 | 55 | 50 | 168 | 273 |
| 8 | 55 | 52 | 166 | 273 |
| 9 | 55 | 51 | 167 | 273 |
| 10 | 55 | 50 | 168 | 273 |

## Check categories

All ten samples use the same Full Story check configuration. Source support
affects progression eligibility, not these existing IDs or native check meanings.

| Category | Checks |
|---|---:|
| Maps | 33 |
| Settlements | 18 |
| Mutant First Kills | 25 |
| Faction First Kills | 13 |
| Artefacts | 66 |
| Quest Types | 13 |
| Story Milestones | 53 |
| Armour Tiers | 4 |
| Weapon Tiers | 6 |
| Knife Tiers | 4 |
| Gear Upgrades | 6 |
| Rank Milestones | 8 |
| Shops | 3 |
| Faction Standing | 4 |
| Shop Purchases | 9 |
| Kill Milestones | 4 |
| Side Task Milestones | 4 |
