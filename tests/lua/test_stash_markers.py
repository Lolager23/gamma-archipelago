from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]


def test_dxml_appends_only_owned_marker_nodes_and_is_idempotent(lua):
    lua.execute("""
        marker_test={has_root=true, patched=false, inserts=0, root={kids={{name='native'}}}}
        RegisterScriptCallback=function(name,fn) marker_test.callback=fn end
        marker_xml={query=function(self,query)
            if query=='map_spots' and marker_test.has_root then return {marker_test.root} end
            if query=='gamma_ap_loot' and marker_test.patched then return {{}} end
            return {}
        end,insertFromXMLString=function(self,text,root,index)
            marker_test.text=text; marker_test.parent=root; marker_test.index=index
            marker_test.inserts=marker_test.inserts+1; marker_test.patched=true
        end}
    """)
    module = lua.globals().load_ap_module(
        str(ROOT / "mod/gamedata/scripts/modxml_gamma_ap_stashes.script")
    )
    module.on_xml_read()
    assert module.registered is True
    test = lua.globals().marker_test
    xml = lua.globals().marker_xml
    module.patch("ui/other.xml", xml)
    test.has_root = False
    module.patch("ui/map_spots.xml", xml)
    assert test.inserts == 0
    test.has_root = True
    for filename in ("ui/map_spots.xml", "ui/map_spots_16.xml", "ui/map_spots_219.xml"):
        test.patched = False
        module.patch(filename, xml)
        module.patch(filename, xml)
    assert test.inserts == 3 and test.index == 2
    assert test.root.kids[1].name == "native"
    nodes = ElementTree.fromstring("<map_spots>" + test.text + "</map_spots>")
    assert {node.tag for node in nodes} == {
        "gamma_ap_loot",
        "gamma_ap_loot_spot",
        "gamma_ap_progression",
        "gamma_ap_progression_spot",
    }
    white = nodes.find("gamma_ap_loot_spot/texture").attrib
    orange = nodes.find("gamma_ap_progression_spot/texture").attrib
    assert (white["r"], white["g"], white["b"]) == ("255", "255", "255")
    assert (orange["r"], orange["g"], orange["b"]) == ("255", "144", "16")
