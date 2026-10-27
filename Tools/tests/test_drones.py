import xml.etree.ElementTree as ET

from oe_ce.constants import ODYSSEY_PACKAGE
from oe_ce.emit_drones import emit_drone_xml, scan_drones, validate_drones

ODYSSEY = """<Defs>
  <ThingDef ParentName="BaseDrone">
    <defName>CAC_Swarmling_Drone</defName>
    <statBases><ArmorRating_Blunt>0.15</ArmorRating_Blunt><ArmorRating_Sharp>0.35</ArmorRating_Sharp></statBases>
    <tools Inherit="False">
      <li>
        <label>stinger</label>
        <capacities><li>Stab</li></capacities>
        <power>6</power>
        <armorPenetration>0.25</armorPenetration>
        <cooldownTime>2.0</cooldownTime>
        <linkedBodyPartsGroup>SpikedShellAttackTool</linkedBodyPartsGroup>
        <extraMeleeDamages><li><def>Scratch</def><amount>3</amount></li></extraMeleeDamages>
      </li>
    </tools>
  </ThingDef>
  <ThingDef ParentName="BaseDrone">
    <defName>OMG_Swarmling_Drone</defName>
    <tools Inherit="False"><li><label>stinger</label><power>6</power></li></tools>
  </ThingDef>
  <PawnKindDef ParentName="BaseDroneKind"><defName>CAC_Swarmling_Drone</defName></PawnKindDef>
</Defs>"""


def _odyssey(tmp_path):
    d = tmp_path / "Defs" / "ThingDefs_Misc" / "Apparel"
    d.mkdir(parents=True)
    (d / "Drones.xml").write_text(ODYSSEY, encoding="utf-8")
    return tmp_path


def test_scan_and_validate_drones(tmp_path):
    scanned = scan_drones(_odyssey(tmp_path))
    assert set(scanned) == {"CAC_Swarmling_Drone", "OMG_Swarmling_Drone"}
    assert validate_drones(scanned) == []
    assert scan_drones(None) == {}


def test_unknown_drone_fails_closed(tmp_path):
    scanned = scan_drones(_odyssey(tmp_path))
    scanned["OE_New_Drone"] = scanned["CAC_Swarmling_Drone"].__class__("OE_New_Drone", None)
    errs = validate_drones(scanned)
    assert any("OE_New_Drone" in e and "DRONES table" in e for e in errs)


def test_emit_drone_ce_tools_armor_and_durability(tmp_path):
    xml = emit_drone_xml(scan_drones(_odyssey(tmp_path)))
    root = ET.fromstring(xml)
    assert {op.get("MayRequire") for op in root} == {ODYSSEY_PACKAGE}
    assert "<ArmorRating_Sharp>2</ArmorRating_Sharp>" in xml
    assert "<ArmorRating_Blunt>3</ArmorRating_Blunt>" in xml
    assert xml.count('<li Class="CombatExtended.ToolCE">') == 2
    assert '<tools Inherit="False">' in xml
    assert "<armorPenetration>" not in xml
    assert "<armorPenetrationSharp>16</armorPenetrationSharp>" in xml
    assert "<armorPenetrationSharp>18</armorPenetrationSharp>" in xml
    assert "<power>10</power>" in xml and "<power>6</power>" not in xml
    assert "<def>Scratch</def>" in xml
    assert "<linkedBodyPartsGroup>SpikedShellAttackTool</linkedBodyPartsGroup>" in xml
    assert xml.count("CombatExtended.CompProperties_ArmorDurability") == 2
