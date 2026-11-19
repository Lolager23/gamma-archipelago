# GAMMA Archipelago setup

This is a private candidate. Expanded engine acceptance remains with the tester;
source and transport tests do not establish a completed GAMMA playthrough.

1. Use the isolated Anomaly/GAMMA development installations, with independent
   appdata and MO2 profiles. Preserve a full folder backup. Never use multiplayer
   saves or deploy into the normal installation.
2. Install the matching add-on through development MO2. Always launch the game
   through that MO2 instance so its other enabled mods also load.
3. Use a separate Archipelago 0.6.8 runtime with Python 3.12. Install the matching
   APWorld and shared companion bundle together, or use the source bootstrap's
   loose world. Do not mix archived and loose copies.
4. Choose a documented preset YAML, set your slot name, and generate/host the
   session. Category switches are independent except explicit generation checks
   for required permissions, early reward access and finite pool size.
5. Start the companion with your slot name and server address, for example:
   `python GammaArchipelagoClient.py --name GammaPlayer --connect 127.0.0.1:38281`.
6. For acceptance, start a fresh Loner in Cordon. The bridge is restricted to
   `D:/AnomalyAP/appdata/archipelago`. Goal/category settings belong to the seed;
   changing them requires a matching new session, not editing a bound save.

Named reward broadcasts appear after receipts apply, including without a PDA.
Join broadcasts also work without a PDA. Optional travel requires separate MCM
preview/confirmation. A received
orange coordinate is not its local protected claim. Zone keys use a randomized
local exploration chain; other rewards use normal multiworld placement.

All Labs means X18, X16, X19, X8 and War Lab. Ordinary underground maps do not
count. Follow the source revision's acceptance/restore guide for save rollback,
errors and updates. No engine-level exactly-once reward guarantee is claimed.
