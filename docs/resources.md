# Resources and baseline policy

Use upstream documentation and source as the implementation references. Record
the commit or release actually used, since documentation and main branches change.

## GAMMA and Anomaly

- [Current GAMMA Discord installation instructions](https://discord.com/channels/912320241713958912/1092852637847789699).
- [Official GAMMA installation wiki](https://github.com/Grokitach/Stalker_GAMMA/wiki/Installing-GAMMA).
- [Official technical support and backup guidance](https://github.com/Grokitach/Stalker_GAMMA/wiki/Technical-Support-FAQ).
- [GAMMA source and mod definitions](https://github.com/Grokitach/Stalker_GAMMA).
- [Current official archive metadata](https://www.mediafire.com/api/1.5/folder/get_content.php?folder_key=agyul0e6fbban&content_type=files&response_format=json).
- [Anomaly 1.5.3 official download](https://www.moddb.com/mods/stalker-anomaly/downloads/stalker-anomaly-153).
- [Monolith engine source](https://github.com/themrdemonized/xray-monolith).
- [Archived engine Lua extension reference](https://github.com/themrdemonized/STALKER-Anomaly-modded-exes).
- [Inspected Monolith callback extension](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/gamedata/scripts/callbacks_gameobject.script).
- [MO2 saved profile priority and duplicate handling](https://github.com/ModOrganizer2/modorganizer/blob/master/src/profile.cpp).
- [Anomaly community scripting guide](https://github.com/robE127/stalker-anomaly-modding-guide).

The installed and extracted `axr_main.script`, game callback registration and
active GAMMA overrides are the final authority for this particular baseline.
Community guide statements must be checked against that code and a live probe.
Implement a separate `gamedata/scripts` add-on rather than editing engine or base
game scripts. Prefer additive callbacks and DLTX changes where applicable.

## Archipelago

- [Adding games](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/docs/adding%20games.md).
- [World API](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/docs/world%20api.md).
- [Network protocol](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/docs/network%20protocol.md).
- [CommonClient](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/CommonClient.py).
- [World test base](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.8/test/bases.py).
- [Release 0.6.8](https://github.com/ArchipelagoMW/Archipelago/releases/tag/0.6.8).

Initial upstream checkout: `0.6.8`, commit
`54803be064fc7e80c4628777ed0b46a9390f255f`. Run our world against real upstream
classes, generator and server. Do not replace the AP framework with test doubles
and call that integration verification.

The GAMMA/Anomaly/AP version combination is pinned after its first successful
in-game smoke test. Update compatibility deliberately on a separate branch.
