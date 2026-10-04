from pathlib import Path

from oe_ce.emit_melee import emit_melee_xml
from oe_ce.emit_pawnkinds import emit_pawnkind_xml
from oe_ce.models import Family, Member
from oe_ce.scan_obsidia import weapon_tags

CORE = Path(r"C:\Projects\Assistant\294100\2519492373\1.6\Core")


def test_weapon_tags_oe_rifle_includes_oesnipergun():
    tags = weapon_tags(CORE, "OE_Rifle")
    assert "OESniperGun" in tags


def test_emit_melee_xml_includes_toolce():
    xml = emit_melee_xml([Member("OE_Sword", "proto")])
    assert "CombatExtended.ToolCE" in xml
    assert "<label>handle</label>" in xml
    assert "<label>blade</label>" in xml
    assert "<power>8</power>" in xml


def test_emit_pawnkind_xml_occ_recruit_loadout():
    fam = Family(
        "cerberus",
        "rifle",
        "ballistic",
        members=[
            Member("OCC_Rifle", "occ"),
            Member("OCC_Revolver", "occ"),
        ],
    )
    xml = emit_pawnkind_xml(CORE, [fam])
    assert "LoadoutPropertiesExtension" in xml
    assert "OCC_Recruit" in xml
    assert "preferredAmmo" not in xml
