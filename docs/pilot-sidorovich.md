# Quick pilot: talk to Sidorovich

The named **pilot** preset now selects **Talk to Sidorovich** (`goal: talk_sidorovich`,
numeric value 6). Start a fresh Loner character in Cordon, speak to Sidorovich,
then close his dialogue. The native `actor_on_leave_dialog` callback identifies
`esc_m_trader`; only that conversation in Cordon completes this goal. Entering
the map, opening trade, other NPCs, invalid IDs and unavailable/refused sessions
do not complete it. Dialogue already completed before connecting is not inferred.
The next normal game poll reports victory; save/reload preserves completion.

Map checks and their rewards remain enabled. The dialogue is a local completion
event, not an extra network check or reward slot. You can finish the quick goal
with the other maps still unchecked, making it suitable for release testing.
The world models a local Cordon conversation event without a psi helmet or quest
key requirement. Native acceptance assumes an available, friendly Sidorovich.

Archipelago controls release policy: `release_mode: goal` permits `!release` from
the companion after victory; `release_mode: auto` releases remaining checks when
victory arrives. A disabled release policy still blocks release. The preset does
not silently override a server's policy. Released checks are server confirmations,
not invented visits to maps, and their items use the normal ordered delivery path.

Goal values 0–5 and the default legacy three-map `pilot_tour` retain their meaning.
Only the named pilot preset changes. Existing seeds, bound characters and the
Brain Scorcher session are not rewritten. Generate a new pilot seed and use a
fresh Dev character; update the APWorld, companion and add-on together.

The quick goal estimate uses a provisional six-minute baseline rather than the
whole-map route; full completion retains the exploration estimate. Both remain
uncalibrated planning heuristics.

Source evidence: the installed `axr_main.script` declares the callback's numeric
NPC ID; active GAMMA `pda.actor_menu_mode(11)` emits it on dialogue close. Mode 10
records the talking NPC explicitly, including Sidorovich. No base script is edited.
Automated regressions cover the callback, save/load, generation and real-server
goal/manual-release/automatic-release behavior. Native game verification is **not
run**, reserved for Owen; no game is launched by the agent.
