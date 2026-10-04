import re
from pathlib import Path

from oe_ce.emit_melee import emit_melee_xml
from oe_ce.emit_pawnkinds import emit_pawnkind_xml
from oe_ce.load import load_catalog
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


def test_elemental_melee_keeps_extra_damage():
    xml = emit_melee_xml([Member("OCC_PowerFist_Fire", "occ")])
    assert "<extraMeleeDamages>" in xml
    assert "<def>Flame</def>" in xml
    acid = emit_melee_xml([Member("OCC_PowerFist_Acid", "occ")])
    assert "<def>OTCAcid</def>" in acid


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


def test_emit_pawnkind_ap_npc_raid_magazine_bump(tmp_path: Path):
    (tmp_path / "ballistic.yaml").write_text(
        "families:\n"
        "  - id: cerberus\n"
        "    type: pistol\n"
        "    class: ballistic\n"
        "    members:\n"
        "      - defName: OCC_Revolver\n"
        "        rung: occ\n"
        "        ap_npc: true\n",
        encoding="utf-8",
    )
    cat = load_catalog(tmp_path)
    assert any(m.ap_npc for fam in cat.families for m in fam.members)
    xml = emit_pawnkind_xml(CORE, cat.families)
    recruit = re.search(
        r'<xpath>Defs/PawnKindDef\[defName="OCC_Recruit"\]</xpath>.*?</Operation>',
        xml,
        re.DOTALL,
    )
    assert recruit is not None
    block = recruit.group(0)
    assert "<min>10</min>" in block
    assert "<max>20</max>" in block
    assert "preferredAmmo" not in xml


def test_raiders_get_multiple_spare_magazines():
    fam = Family(
        "impaler",
        "pistol",
        "ballistic",
        members=[Member("OCC_Revolver", "occ")],
    )
    xml = emit_pawnkind_xml(CORE, [fam])
    recruit = re.search(
        r'<xpath>Defs/PawnKindDef\[defName="OCC_Recruit"\]</xpath>.*?</Operation>',
        xml,
        re.DOTALL,
    )
    assert recruit is not None
    block = recruit.group(0)
    assert "<min>8</min>" in block
    assert "<max>16</max>" in block
