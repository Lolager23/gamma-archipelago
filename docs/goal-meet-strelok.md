# Step 24: meet Strelok

Stack base: #27. Goal `meet_strelok` requires the native first-conversation flag
`living_legend_strelok_start`, given by the final phrase of that dialogue. Reaching
Outskirts, spawning his NPC or receiving a quest key does not qualify. The later
`living_legend_done` flag alone does not substitute for the encounter.

Runtime refuses story-disabled/faction-limited starts and factions outside the
six native Living Legend branches: Loners, Clear Sky, Duty, Freedom, Ecologists
and Mercenaries. The solver models protection, Scorcher shutdown, the Marshes /
Agroprom underground / Zaton / Jupiter / Underpass route and Outskirts encounter.
If quest keys are enabled, Living Legend permission is required. The supported
playtest starting character remains a fresh Loner in Cordon; zone keys also
require that starting area. Native NPC/task availability is not fabricated.

Full verifier: 511 covered tests plus two real-server cases, all coverage gates
pass. Tests distinguish conversation from campaign completion, enforce character
restrictions and fill keyed story seeds. Engine dialogue/goal acceptance is not
run, reserved for Owen after merge. No launch or deployment occurred.
