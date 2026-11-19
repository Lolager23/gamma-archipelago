# Step 21: optional one-time unlock travel

Stack base: #24. New `zone_unlock_travel` defaults off and requires zone keys.
Older configurations may omit it; Python and Lua supply zero, and the default
canonical digest omits this new field to preserve existing seed/save identities.
Turning it on changes the digest and requires this client/add-on version.

MCM offers Preview and Travel buttons. Preview names the actual settlement;
Travel rechecks the exact offer and never runs from menu construction or receipt.
Each received zone key has one complimentary trip. A curated hub in that zone
is preferred, otherwise unlocked Cordon is the fallback. Native smart coordinates
and current NPC rosters are used. Missing/empty/hostile rosters, enemy personal
relations or hostile online NPCs refuse the hub. No blind fixed world coordinates
are invented. Unavailable offers remain unused until a valid hub exists.

The native fast-travel setting must be enabled. Combat, bleeding, radiation,
overweight, emissions and psi storms veto the trip. This AP reward waives
ordinary discovery and guide fees once; it is not a paid guide interaction.
Native zone-key packet guards still apply. Entitlement is saved as consumed
before native travel triggers a save. An explicit false refusal restores it;
an exception remains consumed because travel may already have started. Ordinary
older-save rollback restores the entitlement in that older timeline. No
cross-save exactly-once travel claim is made.

Full verifier: 493 covered tests plus two real-server cases, all independent
coverage gates pass. Tests cover migration/digests, menu delegation, explicit
preview/confirmation, hazards, hostile/missing/changed hubs, failure boundaries
and save/load consumption. Lua executable lines measure 100%; branches are not
measured. Engine settlement arrival and UI acceptance are not run, reserved for
Owen after merge. No launch, deployment or protected-root changes occurred.
