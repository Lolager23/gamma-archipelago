# Step 25: finish Living Legend

Stack base: #28. Goal `living_legend` observes native `living_legend_done`, set
by the terminal return dialogue for each of the six supported faction branches.
The first Strelok conversation and intermediate tasks do not qualify. The same
story-enabled/faction-limited validation from step 24 applies; observed victory
remains saved and monotonic through reload.

The solver has a distinct terminal local event requiring the Strelok encounter
and access to the full supported map roster. This deliberately conservative
route covers campaign travel and the different faction return hubs without
pretending AP controls NPC survival or task scheduling. Quest permission and
protection prerequisites are inherited. Native objectives and final dialogue
remain the game's responsibility; no AP item marks the chain complete.

Full verifier: 511 covered tests plus two real-server cases, all coverage gates
pass. Tests separate first meeting from terminal completion, preserve reload
state and fill a keyed story seed. Engine full-campaign acceptance is not run,
reserved for Owen after merge. No launch or deployment occurred.
