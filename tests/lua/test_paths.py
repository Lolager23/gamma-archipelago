import pytest


@pytest.mark.parametrize(
    "root",
    [
        "D:/AnomalyAP/appdata/",
        "D:\\ANOMALYAP\\appdata\\",
        "d:/anomalyap/bin/..\\appdata\\",
        "D:/AnomalyAP/./appdata/",
        "D:/AnomalyAP//bin/../appdata",
        "D:/AnomalyAP/appdata/temporary/..",
    ],
)
def test_only_equivalent_development_paths_are_canonicalized(lua, root):
    assert lua.globals().gamma_ap_paths.appdata_root(root) == "D:/AnomalyAP/appdata/"


@pytest.mark.parametrize(
    "root",
    [
        None,
        1,
        "D:/Anomaly/appdata/",
        "D:/AnomalyAP/../Anomaly/appdata",
        "D:/AnomalyAP/bin/../../Anomaly/appdata",
        "D:/../AnomalyAP/appdata",
        "C:/AnomalyAP/appdata",
        "../AnomalyAP/appdata",
        "\\\\server\\AnomalyAP\\appdata",
        "D:/AnomalyAP/appdata/extra",
        "D:/AnomalyAP/appdata2",
        "D:/AnomalyAP/appdata.",
        "D:/AnomalyAP/bad:stream/../appdata",
        "D:/AnomalyAP/bad?/../appdata",
        "D:/AnomalyAP/bad\n/../appdata",
        "D:/AnomalyAP/bad /../appdata",
    ],
)
def test_other_roots_traversal_and_ambiguous_windows_paths_are_refused(lua, root):
    assert lua.globals().gamma_ap_paths.appdata_root(root) is None
