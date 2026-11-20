from pathlib import Path
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parents[2]


def rooted_document(lua):
    """DXML queries search descendants; getRoot returns the document element itself."""
    lua.execute("""
        rooted={root={name='map_spots',kids={{name='native'}}},inserts=0,blocked={}}
        RegisterScriptCallback=function(name,fn) rooted.callback=fn end
        rooted_xml={getRoot=function() return rooted.root end,
            getElementName=function(self,node) return node.name end,
            query=function(self,name)
                local found={}
                for _,child in ipairs(rooted.root.kids) do
                    if child.name==name then found[#found+1]=child end
                end
                return found
            end,
            insertFromXMLString=function(self,text,parent,index)
                rooted.inserts=rooted.inserts+1
                rooted.text=(rooted.text or '')..text
                rooted.parent=parent; rooted.index=index
                for name in text:gmatch('<(gamma_ap_[%w_]+)[%s>]') do
                    if not rooted.blocked[name] then table.insert(parent.kids,index,{name=name}) end
                end
            end}
    """)
    module = lua.globals().load_ap_module(
        str(ROOT / "mod/gamedata/scripts/modxml_gamma_ap_stashes.script")
    )
    return module, lua.globals().rooted_xml, lua.globals().rooted


def test_real_dxml_root_is_not_a_descendant_query_result(lua):
    module, xml, document = rooted_document(lua)
    assert len(xml.query(xml, "map_spots")) == 0
    module.patch("ui/map_spots.xml", xml)
    assert document.inserts > 0
    assert len(xml.query(xml, "gamma_ap_loot")) == 1
    assert len(xml.query(xml, "gamma_ap_progression")) == 1


@pytest.mark.parametrize(
    "filename",
    [
        "ui/map_spots.xml",
        "ui/map_spots_16.xml",
        "ui/map_spots_21.xml",
        "ui/map_spots_219.xml",
        "UI\\MAP_SPOTS.XML",
    ],
)
def test_dxml_appends_only_owned_marker_nodes_and_is_idempotent(lua, filename):
    module, xml, test = rooted_document(lua)
    module.on_xml_read()
    assert module.registered is True
    assert module.ready() is False
    module.patch("ui/other.xml", xml)
    assert test.inserts == 0
    module.patch(filename, xml)
    module.patch(filename, xml)
    assert module.ready() is True
    assert test.inserts == 4 and test.index == 5
    assert test.root.kids[1].name == "native"
    nodes = ElementTree.fromstring("<map_spots>" + test.text + "</map_spots>")
    assert {node.tag for node in nodes} == {
        "gamma_ap_loot",
        "gamma_ap_loot_spot",
        "gamma_ap_progression",
        "gamma_ap_progression_spot",
    }
    for kind in ("loot", "progression"):
        texture = nodes.find(f"gamma_ap_{kind}_spot/texture")
        assert texture.text == "gamma_ap_stash_rainbow"
        assert texture.attrib == dict(a="255", r="255", g="255", b="255")


@pytest.mark.parametrize("root", [None, "other"])
def test_missing_or_wrong_root_revokes_previous_readiness(lua, root):
    module, xml, test = rooted_document(lua)
    module.patch("ui/map_spots.xml", xml)
    assert module.ready() is True
    if root is None:
        test.root = None
    else:
        test.root.name = root
    module.patch("ui/map_spots.xml", xml)
    assert module.ready() is False and test.inserts == 4


def test_partial_existing_definitions_are_repaired_without_duplicates(lua):
    module, xml, test = rooted_document(lua)
    lua.execute("table.insert(rooted.root.kids,{name='gamma_ap_loot'})")
    module.patch("ui/map_spots.xml", xml)
    assert module.ready() is True and test.inserts == 3
    for name in (
        "gamma_ap_loot",
        "gamma_ap_loot_spot",
        "gamma_ap_progression",
        "gamma_ap_progression_spot",
    ):
        assert len(xml.query(xml, name)) == 1
    module.patch("ui/other.xml", xml)
    assert module.ready() is True
    module.on_xml_read()
    assert module.ready() is False
    module.patch("ui/map_spots.xml", xml)
    assert module.ready() is True and test.inserts == 3


@pytest.mark.parametrize("duplicate", [False, True])
def test_failed_insert_or_duplicate_definitions_cannot_prove_readiness(lua, duplicate):
    module, xml, test = rooted_document(lua)
    if duplicate:
        lua.execute("""
            table.insert(rooted.root.kids,{name='gamma_ap_loot'})
            table.insert(rooted.root.kids,{name='gamma_ap_loot'})
        """)
    else:
        test.blocked.gamma_ap_progression_spot = True
    module.patch("ui/map_spots.xml", xml)
    assert module.ready() is False
