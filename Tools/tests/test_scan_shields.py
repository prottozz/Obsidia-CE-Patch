from pathlib import Path

from oe_ce.scan_apparel import is_excluded_apparel
from oe_ce.scan_shields import HANDHELD, INNATE, UPGRADE, WORN, scan_shields

CORE_XML = """
  <ThingDef Name="OEArmorBase" Abstract="True">
    <apparel><layers><li>Middle</li><li>Shell</li></layers></apparel>
  </ThingDef>
  <ThingDef Name="OCCArmorMod" ParentName="OEArmorBase">
    <defName>OCC_Armor_M</defName>
  </ThingDef>
  <ThingDef ParentName="OCCArmorMod">
    <defName>OCC_Armor_M_Shield</defName>
    <graphicData><texPath>Things/Armor/OCCShield</texPath></graphicData>
    <comps>
      <li Class="CompProperties_Shield">
        <blocksRangedWeapons>true</blocksRangedWeapons>
      </li>
    </comps>
  </ThingDef>
  <ThingDef Name="OMGArmorBase" ParentName="OEArmorBase" Abstract="True">
    <comps>
      <li Class="CompProperties_Shield">
        <blocksRangedWeapons>false</blocksRangedWeapons>
      </li>
    </comps>
  </ThingDef>
  <ThingDef ParentName="OMGArmorBase">
    <defName>OMG_Armor_Corsair</defName>
  </ThingDef>
  <ThingDef ParentName="OEArmorBase">
    <defName>OCC_Armor</defName>
  </ThingDef>
"""

VEF_XML = """
  <ThingDef Name="OEShieldBase" Abstract="True">
    <thingClass>VEF.Apparels.Apparel_Shield</thingClass>
  </ThingDef>
  <ThingDef ParentName="OEShieldBase">
    <defName>ODC_Shield_Small</defName>
    <graphicData><texPath>Things/Shield/ODC</texPath></graphicData>
    <comps>
      <li Class="VEF.Apparels.CompProperties_Shield" />
    </comps>
  </ThingDef>
  <ThingDef ParentName="ApparelNoQualityBase" Name="OEGrimoireBase" Abstract="True">
    <statBases>
      <EnergyShieldEnergyMax>1.5</EnergyShieldEnergyMax>
    </statBases>
    <comps>
      <li Class="CompProperties_Shield">
        <blocksRangedWeapons>false</blocksRangedWeapons>
      </li>
    </comps>
  </ThingDef>
  <ThingDef ParentName="OEGrimoireBase">
    <defName>OE_Trophy_Grimoire_Defender</defName>
  </ThingDef>
"""

VEF_PATCH = """
<Patch>
  <Operation Class="PatchOperationAdd">
    <xpath>/Defs</xpath>
    <value>
      <ThingDef ParentName="OEShieldBase">
        <defName>OEC_Shield_Small</defName>
        <comps>
          <li Class="VEF.Apparels.CompProperties_Shield" />
        </comps>
      </ThingDef>
    </value>
  </Operation>
</Patch>
"""

BIO_DEFS = """
  <ThingDef>
    <defName>OE_Mech_ArachnaQueen</defName>
    <race><fleshType>Mechanoid</fleshType></race>
    <statBases>
      <EnergyShieldEnergyMax>2.5</EnergyShieldEnergyMax>
    </statBases>
  </ThingDef>
"""

BIO_PATCH = """
<Patch>
  <Operation Class="PatchOperationAdd">
    <xpath>/Defs/ThingDef[defName="OE_Mech_OMG_Dominator"]/statBases</xpath>
    <value>
      <EnergyShieldEnergyMax>1.5</EnergyShieldEnergyMax>
    </value>
  </Operation>
</Patch>
"""

MU_XML = """
  <MU.MechUpgradeDef>
    <defName>OE_MechUpgrade_Module_Shield_O</defName>
    <statFactors>
      <EnergyShieldEnergyMax>2.5</EnergyShieldEnergyMax>
    </statFactors>
  </MU.MechUpgradeDef>
"""


def _write(path: Path, body: str, wrapper: str = "Defs") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<?xml version="1.0" encoding="utf-8"?>\n<{wrapper}>\n{body}\n</{wrapper}>\n',
        encoding="utf-8",
    )


def test_scan_classifies_worn_handheld_innate_upgrade(tmp_path):
    core = tmp_path / "core"
    _write(core / "Defs" / "ThingDefs_Misc" / "Apparel" / "Armor.xml", CORE_XML)
    _write(core / "Defs" / "ThingDefs_Races" / "Empty.xml", "")
    vef = tmp_path / "vef"
    _write(vef / "Core" / "Defs" / "Utility" / "Shields.xml", VEF_XML)
    _write(vef / "Core" / "Patches" / "OEC.xml", VEF_PATCH, wrapper="Patch")
    bio = tmp_path / "bio"
    _write(bio / "Defs" / "ThingDefs_Races" / "Queen.xml", BIO_DEFS)
    _write(bio / "Patches" / "Dominator.xml", BIO_PATCH, wrapper="Patch")
    mu = tmp_path / "mu"
    _write(mu / "Defs" / "Modules.xml", MU_XML)

    found = scan_shields(core, vef=vef, biotech=bio, mech_upgrades=mu)
    assert found["OCC_Armor_M_Shield"].kind == WORN
    assert found["OCC_Armor_M_Shield"].blocks_ranged is True
    assert found["OCC_Armor_M_Shield"].concrete_parent == "OCC_Armor_M"
    assert found["OCC_Armor_M_Shield"].tex_path == "Things/Armor/OCCShield"
    assert found["OMG_Armor_Corsair"].kind == WORN
    assert found["OMG_Armor_Corsair"].blocks_ranged is False
    assert "OCC_Armor" not in found
    assert "OMGArmorBase" not in found
    assert "OEShieldBase" not in found

    assert found["ODC_Shield_Small"].kind == HANDHELD
    assert found["ODC_Shield_Small"].tex_path == "Things/Shield/ODC"
    assert found["OEC_Shield_Small"].kind == HANDHELD
    assert found["OE_Trophy_Grimoire_Defender"].kind == WORN
    assert found["OE_Trophy_Grimoire_Defender"].blocks_ranged is False

    assert found["OE_Mech_ArachnaQueen"].kind == INNATE
    assert found["OE_Mech_OMG_Dominator"].kind == INNATE
    assert found["OE_MechUpgrade_Module_Shield_O"].kind == UPGRADE


def test_oes_shield_excluded_from_apparel_included_in_shields():
    assert is_excluded_apparel("OES_Armor_Shield")
    assert is_excluded_apparel("OCC_Armor_M_Barrier")
