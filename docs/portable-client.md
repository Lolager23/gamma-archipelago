# Installing the packaged companion

Use a separate Archipelago 0.6.8 runtime with Python 3.12 and the pinned runtime
dependencies. Keep it outside both game installations. This package does not
include Archipelago, Python, Anomaly, GAMMA or third-party binaries/assets.

Extract `gamma-archipelago-client.zip` into that separate runtime's root, beside
`CommonClient.py`. Install `gamma.apworld` into its `worlds` directory, then start:

```text
python GammaArchipelagoClient.py --name GammaPlayer --connect 127.0.0.1:38281
```

The companion uses its own runtime-local `user` and `cache` folders. Its game
bridge remains explicitly restricted to `D:/AnomalyAP/appdata/archipelago`.
Deploy the add-on only into the isolated `D:/GAMMAAP` MO2 instance and launch
the development game through MO2 when Owen performs acceptance. The normal
`D:/Anomaly` and `D:/GAMMA` installations are protected.

The APWorld and client bundle must be upgraded together. The client bundle carries
the shared catalogue/protocol/session code, so the APWorld does not depend on this
developer checkout or an editable pip installation. Do not overwrite an existing
shared Archipelago installation. Developers can instead use the documented
bootstrap/launch tools from a checkout; those prioritize that checkout's source.

Keep original appdata/profile backups and the old seed/client/add-on versions
together for rollback. Do not transplant saves between seeds or installations.
Uninstall from a clean non-AP save or restore the full pre-AP backup; removing
the add-on from an active keyed campaign is not a supported way to remove locks.
