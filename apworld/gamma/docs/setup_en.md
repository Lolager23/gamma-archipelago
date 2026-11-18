# Pilot setup

Use Anomaly 1.5.3, the separately installed GAMMA development instance and
Archipelago 0.6.8. Do not install this add-on in an existing multiplayer game.

1. Follow the repository's development-environment guide and run verification.
2. Run `tools/build.py` to create `dist/gamma.apworld` and the MO2 add-on archive.
3. Prepare the separate AP runtime using `tools/bootstrap_ap.py`, generate
   `examples/pilot.yaml` with `tools/run_ap.py generate` and host the output with
   `tools/run_ap.py host --host 127.0.0.1`. See the development guide for commands.
4. Deploy the add-on to the isolated MO2 instance, enable it on `Archipelago DEV`
   and start the companion client with the server address and `GammaPilot` slot.
5. Start a NEW Loner game in Cordon. The companion must connect before the game
   first polls it; a save binds to that seed/slot identity.
6. Visit Garbage and Rostok. Check the server tracker and incoming item messages.

If the seed or slot differs from the save, stop and use the matching save/client.
Do not delete receipt state to silence an error. The pilot replays unacknowledged
items after loading an older save. It does not promise crash-proof exactly-once
delivery, and consumable recovery is still under development.
