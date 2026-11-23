# Local APWorld seed workbench

This web app configures one GAMMA player, displays its exact enabled network
checks and eligible reward types, exports a player YAML and generates a real seed
ZIP through the pinned Archipelago runtime. It does not start GAMMA, MultiServer
or the companion, change saves, or deploy anything into either game installation.

The requested scope is local-only. No hosted copy or external account is required.

## Start

From this branch's checkout, with the documented Python 3.12 environment:

```powershell
& 'D:/GAMMAAPTools/python-env/Scripts/python.exe' tools/bootstrap_ap.py --destination D:/GAMMAAPTools/generator-runtime
& 'D:/GAMMAAPTools/python-env/Scripts/python.exe' tools/run_generator_web.py
```

Open `http://127.0.0.1:38290`. The server binds to loopback only. Use `--port`
to select another local port. Stop with Ctrl+C. No frontend install or build is
required. Node 20 or later is used only for development syntax checks; Python
serves the app and executes generation. The runtime is deliberately separate
from live sessions and the verification runtime.

Choose one of ten presets, edit categories/loadout/goal, and review validation.
Living Legend disables the two later chains' checks and ends at Living Legend.
Full Story enables all three chains and ends at the Operation Afterglow finale.
Existing drafts and exports retain their selected goal until a preset is reapplied.

The `Progressive sphere pacing` control separates progressive reward copies into
distinct actual AP spheres. Progression presets enable it; sparse presets keep
their unrestricted placement. Impossible depth or conflicting fixed placements
reject generation rather than exporting a broken seed. Review batches for Owen
use Living Legend unless another tier is explicitly requested.
Short, standard (initial selection) and extended presets add protected openings.
The tracker/discovery/pacing controls expose hints, next-reward previews, distinct
quotas, exclusions and independent access/combat/grind assumptions. See
[generation pacing](generation-pacing.md) for limits and the actual-seed report.
Milestones accept strictly increasing comma-separated totals. Configuration
validation and catalogue projection call the same Python core as the APWorld;
the browser does not maintain a second generation model. Invalid or undersized
progression pools block exports/generation rather than silently changing options.

The form keeps your draft choices separate from the canonical preview. No Starting
Weapons temporarily overrides firearms/melee choices; turning it off restores
them. New edits invalidate old totals and late responses cannot replace a newer
draft. If the backend stops, generation is disabled and the page reports it;
after restarting it, change a setting to retry without losing the draft.

The preview distinguishes check/reward slots, distinct eligible item IDs and
required progression quantities. Random supply types can repeat or be absent
from a particular seed. Local progression events are excluded from check counts.
Searching filters enabled checks or eligible rewards by name, category or region.

## Reward controls

The Rewards tab groups supplies, stashes/artefacts, access permissions and
faction/skill/carry rewards. Repeatable rewards have a slider plus an exact count
field. Suggested ranges are 0-50, or 0-30 for skill levels. Manual input may go
above that range, subject to the existing 4,000 count limit and available checks.
Turning a category off retains its draft quantity for later re-enabling.

The budget displays required progression, requested/convenience copies and spare
slots. Permissions and progressive tiers are calculated from checks and starting
settings, so their automatic minima cannot be removed with a slider. Separate
switches control exact quantities, varied spare-slot rewards and varied stash
contents. In weighted optional mode exact count controls are inactive. Invalid
counts or insufficient check capacity block YAML/seed export and clear stale
budget figures. See [reward variety](reward-variety-and-controls.md) for content,
legacy compatibility and delivery limits.

## Generate and use

Enter a 1–16 character player name and an unsigned 64-bit decimal seed number.
Names are trimmed to match upstream slot naming. Archipelago is reserved for the
server and is rejected before generation, including case variants.
Generate downloads the actual upstream seed archive, including a spoiler.
The request snapshots the current settings, so later edits do not change an
in-flight run. There is one generator at a time, with a 180-second timeout.
The server requires matching APWorld source/catalogue in the selected runtime.

Local player YAML, generation log and outputs remain under unique folders in
`D:/GAMMAAPTools/generator-sessions`. Failed runs retain their logs there.
No automatic cleanup removes these records. Close the app before managing them.
The downloaded ZIP is an AP session artifact, not a replacement APWorld or mod.

For a multiworld, download the player YAML and combine it with the other players'
YAMLs using the existing Archipelago generation workflow. This first web version
generates one GAMMA slot directly; it does not host a multiworld server or accept
arbitrary uploaded player files. Follow the development guide to host and connect.

## Estimated playtime

The calculator provides a goal-route range, a full-check range and a session
count. It exposes pace, travel, task, artefact, kill-rate, session-length and
additional multiplayer-wait assumptions. Model v1 uses six provisional goal
baselines, a half-hour allowance per AP equipment lock, and a provisional 60-hour
rank-completion floor. Highest kill/task totals count once; overlapping activities
use their maximum rather than summing every check. Full completion adds travel.

Bounds are 60–160% scenarios. They are **uncalibrated heuristics**, not measured
GAMMA playtime, confidence intervals, generation reachability proofs or guarantees.
Encounter luck, faction access, deaths, tasks and multiworld waiting can exceed
them. Reward placement, crashes and other mods are not simulated. Calibrate the
constants only after recording real playthroughs and keep the model versioned.

## Boundaries and tests

The HTTP boundary allows fixed assets/API routes, rejects foreign Host/Origin
headers, requires bounded JSON requests and never accepts filesystem paths or
shell commands from the browser. It deliberately exposes no LAN listener, CORS
access, game controls or arbitrary file downloads. A local user owns the process;
it is not an Internet-facing server. Source is split into catalogue projection,
playtime estimates, generation execution, HTTP transport and focused browser modules.
Incomplete request bodies are rejected, stalled bodies time out after five
seconds, and JSON nesting is capped at 16 levels before decoding. Quoted brackets
and escaped quotes do not count as nesting.

Regression tests exercise every preset's IDs, dynamic milestone IDs, invalid
options/pool sizes/names/assumptions/seeds, generation failures/timeouts/busy state,
runtime mismatch and real HTTP export/rejection paths. An untraced integration
case generates and inspects a real AP seed ZIP. Python per-module line and branch
coverage gates still apply. Browser interaction evidence is separate from these
tests and from GAMMA acceptance.

The expanded web matrix checks all ten presets at seed 0 and the maximum 64-bit
seed against exact generated IDs/settings, repeated-seed placements, concurrent
HTTP generation refusal and subsequent recovery. Node built-in regression
tests exercise draft/preview isolation, stale responses, preset copies, names and
seed bounds. They run with the complete verifier; no frontend test dependencies
or numeric JavaScript coverage claim are introduced.

The nested HTTP handler is kept together to make request/response ownership
explicit. Its factory exceeds the 40-line guideline because it defines the small
HTTP methods; it does not own generation or planner state. The synchronous
generation function keeps subprocess/log/output failure cleanup in one boundary.
