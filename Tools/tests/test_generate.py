import shutil
from pathlib import Path

import pytest

from oe_ce.generate import generate

ROOT = Path(__file__).resolve().parents[2]


def _write_minimal_core(core: Path, *, with_apparel: bool = True) -> None:
    weapons = core / "Defs" / "ThingDefs_Misc" / "Weapons"
    weapons.mkdir(parents=True)
    (weapons / "Rifles.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef>
    <defName>OE_Rifle</defName>
    <verbs><li /></verbs>
    <tools><li /></tools>
    <weaponTags><li>OE_ProtoGun</li></weaponTags>
  </ThingDef>
  <ThingDef>
    <defName>OCC_Rifle</defName>
    <verbs><li /></verbs>
    <tools><li /></tools>
    <weaponTags><li>OE_OccGun</li></weaponTags>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    pawnkinds = core / "Defs" / "PawnKinds"
    pawnkinds.mkdir(parents=True)
    races = core / "Defs" / "ThingDefs_Races"
    races.mkdir(parents=True)
    (races / "Races.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef>
    <defName>OE_Direwolf</defName>
    <race></race>
  </ThingDef>
  <ThingDef>
    <defName>OE_Mech_DarkCrusader</defName>
    <race><fleshType>Mechanoid</fleshType></race>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    if not with_apparel:
        return
    apparel = core / "Defs" / "ThingDefs_Misc" / "Apparel"
    apparel.mkdir(parents=True)
    (apparel / "Armor.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef Name="OEArmorBase" Abstract="True">
    <apparel><layers><li>Middle</li><li>Shell</li></layers></apparel>
  </ThingDef>
  <ThingDef Name="OCCArmorMod" ParentName="OEArmorBase">
    <defName>OCC_Armor_M</defName>
  </ThingDef>
  <ThingDef ParentName="OCCArmorMod">
    <defName>OCC_Armor_M_Shield</defName>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )


def test_generate_cerberus_files(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "fake_core"
    _write_minimal_core(core)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    monkeypatch.setenv("OE_CE_ALLOW_PARTIAL", "1")
    generate(tmp_path)
    ammo = (tmp_path / "Defs" / "Ammo" / "OE_Ammo.xml").read_text(encoding="utf-8")
    guns = (tmp_path / "Patches" / "Weapons" / "OE_Ranged.xml").read_text(encoding="utf-8")
    assert "Ammo_OE_rifle_ballistic_standard" in ammo
    assert "AmmoSet_OE_OE_Rifle" in ammo
    assert "OE_Rifle" in guns
    assert "OCC_Rifle" in guns


def test_generate_writes_apparel_patches(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "fake_core"
    _write_minimal_core(core)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    monkeypatch.setenv("OE_CE_ALLOW_PARTIAL", "1")
    generate(tmp_path)
    armor = (tmp_path / "Patches" / "Apparel" / "OE_Armor.xml").read_text(encoding="utf-8")
    helmets = (tmp_path / "Patches" / "Apparel" / "OE_Helmets.xml").read_text(encoding="utf-8")
    assert 'defName="OCC_Armor_M"]' in armor
    assert "OCC_Armor_M_Shield" not in armor
    assert "CombatExtended.PartialArmorExt" in armor
    assert 'defName="OCC_Helmet"]' in helmets
    assert "CarryWeight" not in helmets


def test_generate_fails_without_core_weapons(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "empty_core"
    core.mkdir()
    (core / "Defs" / "PawnKinds").mkdir(parents=True)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    with pytest.raises(FileNotFoundError, match="weapons"):
        generate(tmp_path)


def test_generate_writes_race_patches(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "fake_core"
    _write_minimal_core(core)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    monkeypatch.setenv("OE_CE_ALLOW_PARTIAL", "1")
    generate(tmp_path)
    animals = (tmp_path / "Patches" / "Races" / "OE_Animals.xml").read_text(encoding="utf-8")
    mechs = (tmp_path / "Patches" / "Races" / "OE_Mechanoids.xml").read_text(encoding="utf-8")
    assert 'defName="OE_Direwolf"]' in animals
    assert "CombatExtended.RacePropertiesExtensionCE" in animals
    assert 'defName="OE_Mech_DarkCrusader"]' in mechs
    assert "CompAmmoGiver" not in mechs
    assert 'MayRequire="Ludeon.RimWorld.Biotech"' in mechs
    armor = (tmp_path / "Patches" / "Apparel" / "OE_Armor.xml").read_text(encoding="utf-8")
    assert 'defName="OCC_Armor_M"]' in armor


def test_generate_fails_without_core_races(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "no_races_core"
    _write_minimal_core(core)
    shutil.rmtree(core / "Defs" / "ThingDefs_Races")
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    with pytest.raises(FileNotFoundError, match="races"):
        generate(tmp_path)


def test_generate_fails_without_core_apparel(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "no_apparel_core"
    _write_minimal_core(core, with_apparel=False)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    with pytest.raises(FileNotFoundError, match="apparel"):
        generate(tmp_path)
