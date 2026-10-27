import os
import shutil
from pathlib import Path

import pytest

from oe_ce.constants import DEFAULT_OBSIDIA_ANOMALY
from oe_ce.generate import generate

ROOT = Path(__file__).resolve().parents[2]
ANOMALY = Path(os.environ.get("OBSIDIA_ANOMALY", DEFAULT_OBSIDIA_ANOMALY))


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
    bodies = core / "Defs" / "Bodies"
    bodies.mkdir(parents=True)
    (bodies / "Bodies.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <BodyDef>
    <defName>OESlimeLike</defName>
    <corePart>
      <def>Body</def>
      <parts>
        <li>
          <def>Stomach</def>
          <coverage>0.05</coverage>
          <depth>Inside</depth>
        </li>
        <li>
          <def>Eye</def>
          <coverage>0.05</coverage>
        </li>
      </parts>
    </corePart>
  </BodyDef>
</Defs>
""",
        encoding="utf-8",
    )
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
    ammo = (tmp_path / "1.7" / "Defs" / "Ammo" / "OE_Ammo.xml").read_text(encoding="utf-8")
    guns = (tmp_path / "1.7" / "Patches" / "Weapons" / "OE_Ranged.xml").read_text(encoding="utf-8")
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
    armor = (tmp_path / "1.7" / "Patches" / "Apparel" / "OE_Armor.xml").read_text(encoding="utf-8")
    helmets = (tmp_path / "1.7" / "Patches" / "Apparel" / "OE_Helmets.xml").read_text(encoding="utf-8")
    assert 'defName="OCC_Armor_M"]' in armor
    assert "OCC_Armor_M_Shield" not in armor
    assert "CombatExtended.PartialArmorExt" in armor
    assert 'defName="OCC_Helmet"]' in helmets
    assert "CarryWeight" not in helmets
    shields = (tmp_path / "1.7" / "Patches" / "Apparel" / "OE_Shields.xml").read_text(encoding="utf-8")
    race_shields = (tmp_path / "1.7" / "Patches" / "Races" / "OE_Shields.xml").read_text(
        encoding="utf-8"
    )
    upgrades = tmp_path / "1.7" / "Patches" / "Misc" / "OE_MechUpgrades.xml"
    assert 'defName="OCC_Armor_M_Shield"]' in shields
    assert 'MayRequire="Ludeon.RimWorld.Biotech"' in race_shields
    assert upgrades.is_file()
    assert "MU.MechUpgradeDef" in upgrades.read_text(encoding="utf-8")
    belts = (tmp_path / "1.7" / "Patches" / "Apparel" / "OE_GrenadeBelts.xml").read_text(
        encoding="utf-8"
    )
    assert "OTC_GrenadeBelt_Acid" in belts
    assert "Verb_LaunchProjectileStaticCE" in belts
    assert "forcedMissRadius" not in belts


def test_generate_writes_body_patches(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "fake_core"
    _write_minimal_core(core)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    monkeypatch.setenv("OBSIDIA_BIOTECH", str(tmp_path / "nope"))
    monkeypatch.setenv("OBSIDIA_ANOMALY", str(tmp_path / "nope"))
    monkeypatch.setenv("OBSIDIA_IDEOLOGY", str(tmp_path / "nope"))
    monkeypatch.setenv("OBSIDIA_ROYALTY", str(tmp_path / "nope"))
    monkeypatch.setenv("OE_CE_ALLOW_PARTIAL", "1")
    generate(tmp_path)
    animals = tmp_path / "1.7" / "Patches" / "Bodies" / "OE_Animals.xml"
    mechs = tmp_path / "1.7" / "Patches" / "Bodies" / "OE_Mechanoids.xml"
    assert animals.is_file()
    assert mechs.is_file()


def test_generated_bodies_cover_arachna_and_dominator():
    animals = (ROOT / "1.7" / "Patches" / "Bodies" / "OE_Animals.xml").read_text(encoding="utf-8")
    mechs = (ROOT / "1.7" / "Patches" / "Bodies" / "OE_Mechanoids.xml").read_text(encoding="utf-8")
    assert 'defName="OEArachnaLike"' in animals
    assert "CoveredByNaturalArmor" in animals
    assert 'defName="OEDominator"' in mechs
    assert "<coverage>0.18</coverage>" in mechs
    assert 'MayRequire="Ludeon.RimWorld.Biotech"' in mechs
    assert 'MayRequire="Ludeon.RimWorld.Anomaly"' in animals


def test_generate_writes_dlc_race_wraps(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "fake_core"
    _write_minimal_core(core)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    monkeypatch.setenv("OE_CE_ALLOW_PARTIAL", "1")
    generate(tmp_path)
    animals = tmp_path / "1.7" / "Patches" / "Races" / "OE_Animals.xml"
    mechs = tmp_path / "1.7" / "Patches" / "Races" / "OE_Mechanoids.xml"
    assert animals.is_file()
    assert mechs.is_file()


@pytest.mark.skipif(not ANOMALY.is_dir(), reason="Obsidia Anomaly not installed")
def test_generated_animals_wraps_anomaly_when_tree_present():
    animals = (ROOT / "1.7" / "Patches" / "Races" / "OE_Animals.xml").read_text(encoding="utf-8")
    mechs = (ROOT / "1.7" / "Patches" / "Races" / "OE_Mechanoids.xml").read_text(encoding="utf-8")
    assert 'MayRequire="Ludeon.RimWorld.Anomaly"' in animals
    assert "OE_ChaosSlime_Invincible" in animals
    assert "<ArmorRating_Sharp>14</ArmorRating_Sharp>" in animals
    assert 'MayRequire="Ludeon.RimWorld.Ideology"' in animals
    assert "OE_Dryad_Synthesis" in animals
    assert "OE_Mech_Maid" in mechs
    assert 'MayRequire="Ludeon.RimWorld.Biotech"' in mechs
    assert "forcedMissRadius" not in animals


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
    race_yaml = tmp_path / "catalog" / "races.yaml"
    race_yaml.write_text(
        race_yaml.read_text(encoding="utf-8").replace(
            "  - id: chaos_lord\n    analogue: diabolus",
            "  - id: chaos_lord\n    analogue: diabolus\n    mayRequire: Ludeon.RimWorld.Biotech",
        ),
        encoding="utf-8",
    )
    core = tmp_path / "fake_core"
    _write_minimal_core(core)
    biotech = tmp_path / "fake_biotech"
    races = biotech / "Defs" / "ThingDefs_Races"
    races.mkdir(parents=True)
    (races / "Mechs.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef>
    <defName>OE_Mech_ChaosLord</defName>
    <race><fleshType>Mechanoid</fleshType></race>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    monkeypatch.setenv("OBSIDIA_BIOTECH", str(biotech))
    monkeypatch.setenv("OBSIDIA_ANOMALY", str(tmp_path / "no_anomaly"))
    monkeypatch.setenv("OBSIDIA_IDEOLOGY", str(tmp_path / "no_ideology"))
    monkeypatch.setenv("OE_CE_ALLOW_PARTIAL", "1")
    generate(tmp_path)
    animals = (tmp_path / "1.7" / "Patches" / "Races" / "OE_Animals.xml").read_text(encoding="utf-8")
    mechs = (tmp_path / "1.7" / "Patches" / "Races" / "OE_Mechanoids.xml").read_text(encoding="utf-8")
    assert 'defName="OE_Direwolf"]' in animals
    assert "CombatExtended.RacePropertiesExtensionCE" in animals
    assert 'defName="OE_Mech_DarkCrusader"]' in mechs
    assert "CompAmmoGiver" not in mechs
    assert 'MayRequire="Ludeon.RimWorld.Biotech"' in mechs
    armor = (tmp_path / "1.7" / "Patches" / "Apparel" / "OE_Armor.xml").read_text(encoding="utf-8")
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


def test_generate_wraps_royalty_apparel(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "fake_core"
    _write_minimal_core(core)
    royalty = tmp_path / "fake_royalty"
    apparel = royalty / "Defs" / "ThingDefs_Misc" / "Apparel"
    apparel.mkdir(parents=True)
    (apparel / "Armor.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef Name="OECArmorBase" Abstract="True">
    <apparel><layers><li>Middle</li><li>Shell</li></layers></apparel>
  </ThingDef>
  <ThingDef ParentName="OECArmorBase">
    <defName>OEC_Armor</defName>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    monkeypatch.setenv("OBSIDIA_ROYALTY", str(royalty))
    monkeypatch.setenv("OE_CE_ALLOW_PARTIAL", "1")
    generate(tmp_path)
    armor = (tmp_path / "1.7" / "Patches" / "Apparel" / "OE_Armor.xml").read_text(encoding="utf-8")
    assert 'defName="OEC_Armor"]' in armor
    assert 'MayRequire="Ludeon.RimWorld.Royalty"' in armor
    inner = armor.split("<operations>")[1].split("</operations>")[0]
    assert "<li Class=" in inner
    assert "<Operation Class=" not in inner
    assert 'defName="OCC_Armor_M"]' in armor.split('MayRequire="Ludeon.RimWorld.Royalty"')[0]


def _optional_blocks(path: Path) -> dict[str, tuple[str | None, str]]:
    import xml.etree.ElementTree as ET

    out = {}
    for op in ET.parse(path).getroot():
        xpath = op.findtext("xpath") or ""
        if op.get("MayRequire") and xpath.startswith('Defs/ThingDef[defName="'):
            name = xpath.split('"')[1]
            out[name] = (op.get("MayRequire"), ET.tostring(op, encoding="unicode"))
    return out


def test_committed_dlc_apparel_is_wrapped_and_plated():
    armor = _optional_blocks(ROOT / "1.7" / "Patches" / "Apparel" / "OE_Armor.xml")
    helmets = _optional_blocks(ROOT / "1.7" / "Patches" / "Apparel" / "OE_Helmets.xml")
    pkg, turret = armor["OCC_Armor_M_Turret"]
    assert pkg == "Ludeon.RimWorld.Anomaly"
    assert "<ArmorRating_Sharp>26</ArmorRating_Sharp>" in turret
    assert "PartialArmorExt" not in turret
    pkg, priest = armor["CAC_PriestArmor"]
    assert pkg == "Ludeon.RimWorld.Anomaly"
    assert "<ArmorRating_Sharp>28</ArmorRating_Sharp>" in priest
    assert "PartialArmorExt" in priest
    pkg, swarm = armor["OMG_Armor_Swarmling"]
    assert pkg == "Ludeon.RimWorld.Odyssey"
    assert "<ArmorRating_Sharp>30</ArmorRating_Sharp>" in swarm
    pkg, kid = armor["OE_Armor_Kid"]
    assert pkg == "Ludeon.RimWorld.Biotech"
    assert "<Mass>18</Mass>" in kid and "CarryWeight" not in kid
    pkg, mech = helmets["EGO_Helmet_Exohelm_Mechanitor"]
    assert pkg == "Ludeon.RimWorld.Biotech"
    assert "<ArmorRating_Sharp>22</ArmorRating_Sharp>" in mech
    assert helmets["OMG_Trophy_Helmet_Necrospark"][0] == "Ludeon.RimWorld.Anomaly"


def test_committed_apparel_verbs_cover_dlc_deploys():
    path = ROOT / "1.7" / "Patches" / "Apparel" / "OE_ApparelVerbs.xml"
    blocks = _optional_blocks(path)
    for name in (
        "OCC_Armor_M_Turret",
        "OTC_Armor_M_Turret",
        "OMG_Armor_Commando",
        "CAC_PriestArmor",
        "OMG_Trophy_Helmet_Firemark",
        "OMG_Trophy_Helmet_Necrospark",
        "Grenade_Armor_OTC_TurretPack_EMP",
        "Grenade_OMG_Deadlife",
    ):
        assert blocks[name][0] == "Ludeon.RimWorld.Anomaly", name
    pkg, ego = blocks["EGO_Armor_Shell_Mechanitor"]
    assert pkg == "Ludeon.RimWorld.Biotech"
    assert "Verb_LaunchProjectileStaticCE" in ego
    assert blocks["OTC_Armor_M_Turret"][1].count("Verb_LaunchProjectileStaticCE") == 4
    assert "OMG_Armor_Swarmling" not in blocks
