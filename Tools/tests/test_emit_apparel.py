import xml.etree.ElementTree as ET

from oe_ce.apparel_models import ApparelMember, ApparelSet
from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.emit_apparel import emit_apparel_xml
from oe_ce.scan_apparel import CoreApparel

CORE = {
    "OCC_Armor": CoreApparel("OCC_Armor", ARMOR),
    "OCC_Armor_M": CoreApparel("OCC_Armor_M", ARMOR),
    "OCC_Armor_M_Spacer": CoreApparel("OCC_Armor_M_Spacer", ARMOR, "OCC_Armor_M"),
    "OCC_Helmet": CoreApparel("OCC_Helmet", HELMET),
}


def test_occ_armor_gets_marine_stats_carry_and_coverage():
    xml = emit_apparel_xml([ApparelSet("occ", "occ", [ApparelMember("OCC_Armor")])], ARMOR, CORE)
    assert '<xpath>Defs/ThingDef[defName="OCC_Armor"]/statBases/ArmorRating_Sharp</xpath>' in xml
    assert "<ArmorRating_Sharp>20</ArmorRating_Sharp>" in xml
    assert "<ArmorRating_Blunt>45</ArmorRating_Blunt>" in xml
    assert "<ArmorRating_Heat>0.54</ArmorRating_Heat>" in xml
    assert "<Mass>50</Mass>" in xml
    assert "<Bulk>100</Bulk>" in xml
    assert "<WornBulk>15</WornBulk>" in xml
    assert "<CarryWeight>80</CarryWeight>" in xml
    assert "<CarryBulk>10</CarryBulk>" in xml
    assert "CombatExtended.PartialArmorExt" in xml
    assert "<li>Arm</li>" in xml
    assert "<ArmorRating_Sharp>0.90</ArmorRating_Sharp>" in xml


def test_missing_stat_nodes_are_added_not_assumed():
    xml = emit_apparel_xml([ApparelSet("occ", "occ", [ApparelMember("OCC_Armor")])], ARMOR, CORE)
    assert "<statBases />" in xml
    assert "<equippedStatOffsets />" in xml
    assert 'Class="PatchOperationConditional"' in xml
    assert '<nomatch Class="PatchOperationAdd">' in xml
    assert '<match Class="PatchOperationReplace">' in xml


def test_helmet_uses_helmet_template_and_no_carry():
    xml = emit_apparel_xml([ApparelSet("occ", "occ", [ApparelMember("OCC_Helmet")])], HELMET, CORE)
    assert "<ArmorRating_Sharp>16</ArmorRating_Sharp>" in xml
    assert "<ArmorRating_Blunt>36</ArmorRating_Blunt>" in xml
    assert "<li>Eye</li>" in xml
    assert "<li>Arm</li>" not in xml
    assert "CarryWeight" not in xml
    assert "equippedStatOffsets" not in xml


def test_child_of_catalogued_parent_gets_stats_but_no_second_extension():
    s = ApparelSet(
        "occ",
        "occ_reforge",
        [ApparelMember("OCC_Armor_M"), ApparelMember("OCC_Armor_M_Spacer")],
    )
    xml = emit_apparel_xml([s], ARMOR, CORE)
    assert xml.count("PatchOperationAddModExtension") == 1
    assert '<xpath>Defs/ThingDef[defName="OCC_Armor_M"]</xpath>' in xml
    assert (
        '<xpath>Defs/ThingDef[defName="OCC_Armor_M_Spacer"]/statBases/ArmorRating_Sharp</xpath>'
        in xml
    )
    assert "<ArmorRating_Sharp>26</ArmorRating_Sharp>" in xml


def test_output_is_valid_sorted_patch():
    s = ApparelSet(
        "occ",
        "occ",
        [ApparelMember("OCC_Armor_M", "occ_reforge"), ApparelMember("OCC_Armor")],
    )
    xml = emit_apparel_xml([s], ARMOR, CORE)
    root = ET.fromstring(xml.split("?>", 1)[1])
    assert root.tag == "Patch"
    assert xml.index('defName="OCC_Armor"]') < xml.index('defName="OCC_Armor_M"]')
