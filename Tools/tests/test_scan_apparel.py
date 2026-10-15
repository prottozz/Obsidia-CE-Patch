import os
from pathlib import Path

import pytest

from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.constants import DEFAULT_OBSIDIA_CORE
from oe_ce.scan_apparel import is_excluded_apparel, scan_core_apparel

CORE = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))

FIXTURE = """
  <ThingDef Name="OEArmorBase" Abstract="True">
    <apparel><layers><li>Middle</li><li>Shell</li></layers></apparel>
  </ThingDef>
  <ThingDef Name="OEHelmetBase" Abstract="True">
    <apparel><layers><li>Overhead</li></layers></apparel>
  </ThingDef>
  <ThingDef Name="OEUniformBase" Abstract="True">
    <apparel><layers><li>OnSkin</li></layers></apparel>
  </ThingDef>
  <ThingDef Name="OCCArmorMod" ParentName="OEArmorBase">
    <defName>OCC_Armor_M</defName>
  </ThingDef>
  <ThingDef ParentName="OCCArmorMod">
    <defName>OCC_Armor_M_Spacer</defName>
  </ThingDef>
  <ThingDef ParentName="OCCArmorMod">
    <defName>OCC_Armor_M_Shield</defName>
  </ThingDef>
  <ThingDef ParentName="OEHelmetBase">
    <defName>OCC_Helmet</defName>
  </ThingDef>
  <ThingDef ParentName="OEHelmetBase">
    <defName>ODC_Helmet_Miner</defName>
  </ThingDef>
  <ThingDef ParentName="OEUniformBase">
    <defName>OE_Uniform_Military</defName>
  </ThingDef>
  <ThingDef>
    <defName>Grenade_Armor_OTC_Acid</defName>
  </ThingDef>
"""


def _write_apparel(core: Path, body: str) -> Path:
    apparel = core / "Defs" / "ThingDefs_Misc" / "Apparel"
    apparel.mkdir(parents=True, exist_ok=True)
    (apparel / "Fixture.xml").write_text(
        f'<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n{body}\n</Defs>\n',
        encoding="utf-8",
    )
    return core


def test_excludes():
    for name in (
        "OTC_Armor_M_Grenadier_Fire",
        "OES_Armor_Barrier",
        "OCC_Armor_M_Shield",
        "Grenade_Armor_OTC_Acid",
        "ODC_Helmet_Beastmaster",
        "EGO_Armor_Shell_Worker",
        "OE_Uniform_Worker",
    ):
        assert is_excluded_apparel(name), name
    for name in ("OCC_Armor", "ODC_Armor_Recon_Smoker", "OMG_Trophy_Helmet_Hellrain"):
        assert not is_excluded_apparel(name), name


def test_scan_classifies_and_records_concrete_parent(tmp_path):
    core = _write_apparel(tmp_path, FIXTURE)
    found = scan_core_apparel(core)
    assert set(found) == {"OCC_Armor_M", "OCC_Armor_M_Spacer", "OCC_Helmet"}
    assert found["OCC_Armor_M"].kind == ARMOR
    assert found["OCC_Armor_M"].concrete_parent is None
    assert found["OCC_Armor_M_Spacer"].kind == ARMOR
    assert found["OCC_Armor_M_Spacer"].concrete_parent == "OCC_Armor_M"
    assert found["OCC_Helmet"].kind == HELMET


def test_scan_fails_without_apparel_dir(tmp_path):
    with pytest.raises(FileNotFoundError, match="apparel"):
        scan_core_apparel(tmp_path)


def test_real_core_apparel_counts():
    found = scan_core_apparel(CORE)
    armor = {n for n, a in found.items() if a.kind == ARMOR}
    helmets = {n for n, a in found.items() if a.kind == HELMET}
    assert len(armor) == 32
    assert len(helmets) == 32
    assert "EGO_Armor_Suit" in armor
    assert "OMG_Trophy_Helmet_Forgemind" in helmets
    assert found["OCC_Armor_M_Spacer"].concrete_parent == "OCC_Armor_M"
    assert "OCC_Armor_M_Shield" not in found
    assert "OE_Uniform_Military" not in found
