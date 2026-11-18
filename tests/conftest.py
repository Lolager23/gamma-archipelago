"""Use only the private AP runtime prepared by tools/bootstrap_ap.py."""

import os
import sys
from pathlib import Path

RUNTIME = Path(os.environ.get("AP_RUNTIME_ROOT", "D:/GAMMAAPTools/ap-runtime"))
os.environ["SKIP_REQUIREMENTS_UPDATE"] = "1"
os.environ["AP_TEST_WORLDS"] = "gamma,apquest"
if RUNTIME.is_dir():
    sys.path.insert(0, str(RUNTIME))
    import Utils

    Utils.user_path.cached_path = str(RUNTIME / "user")
    Utils.cache_path.cached_path = str(RUNTIME / "cache")
    Path(Utils.user_path()).mkdir(exist_ok=True)
    import settings

    settings.skip_autosave = True
