import os
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from oe_ce.constants import (
    BIOTECH_PACKAGE,
    DEFAULT_OBSIDIA_BIOTECH,
    DEFAULT_OBSIDIA_CORE,
    DEFAULT_OBSIDIA_ODYSSEY,
    DEFAULT_OBSIDIA_ROYALTY,
    ODYSSEY_PACKAGE,
    ROYALTY_PACKAGE,
)
from oe_ce.emit_turrets import emit_ammo_net_xml, emit_turret_xml
from oe_ce.scan_turrets import scan_turrets
from oe_ce.turret_models import TurretCatalog, TurretGun, load_turret_catalog
from oe_ce.validate_turrets import validate_turret_catalog

ROOT = Path(__file__).resolve().parents[2]
CORE = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))

CORE_DEFS = """<Defs>
  <ThingDef Name="OE_TurretBase" Abstract="True"><thingClass>Building_TurretGun</thingClass></ThingDef>
  <ThingDef Name="OE_TurretBase_Small" ParentName="OE_TurretBase" Abstract="True"/>
  <ThingDef Name="OE_TurretBase_Ceiling" ParentName="OE_TurretBase" Abstract="True"><fillPercent>0.15</fillPercent></ThingDef>
  <ThingDef ParentName="OE_TurretBase_Small">
    <defName>ODC_Turret_Small</defName>
    <comps>
      <li Class="CompProperties_Refuelable">
        <fuelFilter><thingDefs><li>OE_AmmoKit</li></thingDefs></fuelFilter>
        <fuelCapacity>300</fuelCapacity>
        <fuelMultiplier>12</fuelMultiplier>
      </li>
      <li Class="CompProperties_Explosive"/>
    </comps>
    <building><turretGunDef>ODC_TurretGun_Small</turretGunDef></building>
  </ThingDef>
  <ThingDef ParentName="OE_TurretBase_Ceiling">
    <defName>ODC_Turret_Ceiling</defName>
    <comps>
      <li Class="CompProperties_Refuelable">
        <fuelFilter><thingDefs><li>OE_AmmoKit</li></thingDefs></fuelFilter>
        <fuelCapacity>200</fuelCapacity>
        <fuelMultiplier>8</fuelMultiplier>
      </li>
    </comps>
    <building><turretGunDef>ODC_Gun_TacticalTurret</turretGunDef></building>
  </ThingDef>
  <ThingDef ParentName="BuildingBase">
    <defName>ODC_Turret_TacticalTurret</defName>
    <building><turretGunDef>ODC_Gun_TacticalTurret</turretGunDef></building>
  </ThingDef>
  <ThingDef ParentName="OE_TurretBase_Small">
    <defName>EGO_Turret_Small_SMG</defName>
    <building><turretGunDef>EGO_TurretGun_Small_SMG</turretGunDef></building>
  </ThingDef>
  <ThingDef ParentName="BaseWeaponTurret"><defName>ODC_TurretGun_Small</defName>
    <verbs><li><defaultProjectile>ODC_TurretBullet_Small</defaultProjectile><burstShotCount>6</burstShotCount></li></verbs></ThingDef>
  <ThingDef ParentName="BaseWeaponTurret"><defName>ODC_Gun_TacticalTurret</defName>
    <verbs><li><defaultProjectile>Bullet_ODC_R</defaultProjectile><burstShotCount>5</burstShotCount></li></verbs></ThingDef>
  <ThingDef ParentName="BaseWeaponTurret"><defName>EGO_TurretGun_Small_SMG</defName>
    <verbs><li><defaultProjectile>Bullet_EGO_SMG</defaultProjectile></li></verbs></ThingDef>
</Defs>"""

ROYALTY_DEFS = """<Defs>
  <ThingDef ParentName="OE_TurretBase_Small">
    <defName>OEC_Turret_Small</defName>
    <comps>
      <li Class="CompProperties_Refuelable">
        <fuelFilter><thingDefs><li>OE_AmmoKit</li></thingDefs></fuelFilter>
        <fuelCapacity>200</fuelCapacity>
        <fuelMultiplier>2.86</fuelMultiplier>
      </li>
    </comps>
    <building><turretGunDef>OEC_TurretGun_Small</turretGunDef></building>
  </ThingDef>
  <ThingDef ParentName="BaseWeaponTurret"><defName>OEC_TurretGun_Small</defName></ThingDef>
</Defs>"""


def _tree(root: Path, body: str) -> Path:
    d = root / "Defs" / "ThingDefs_Buildings"
    d.mkdir(parents=True)
    (d / "T.xml").write_text(body, encoding="utf-8")
    return root


def _scan(tmp_path, royalty=True):
    core = _tree(tmp_path / "core", CORE_DEFS)
    roy = _tree(tmp_path / "royalty", ROYALTY_DEFS) if royalty else None
    return scan_turrets(core, roy)


def _cat() -> TurretCatalog:
    return TurretCatalog(
        guns=[
            TurretGun("ODC_TurretGun_Small", "smg", "emp", "odc_t2", 300, 12),
            TurretGun("ODC_Gun_TacticalTurret", "smg", "ballistic", "odc_t1", 200, 8),
            TurretGun("EGO_TurretGun_Small_SMG", "smg", "ballistic", "bio_t3"),
            TurretGun("OEC_TurretGun_Small", "rifle", "ballistic", "oec", 200, 2.86, ROYALTY_PACKAGE),
        ]
    )


def test_scan_records_fuel_tactical_and_package(tmp_path):
    scan = _scan(tmp_path)
    small = scan.turrets["ODC_Turret_Small"]
    assert (small.gun, small.fuel_capacity, small.kit_shots, small.tactical) == (
        "ODC_TurretGun_Small", 300, 12, False)
    assert small.explosive
    tac = scan.turrets["ODC_Turret_TacticalTurret"]
    assert tac.tactical and tac.fuel_capacity is None
    assert scan.turrets["EGO_Turret_Small_SMG"].fuel_capacity is None
    assert scan.turrets["OEC_Turret_Small"].package == ROYALTY_PACKAGE
    assert scan.guns["ODC_TurretGun_Small"].burst == 6
    assert scan.guns["OEC_TurretGun_Small"].package == ROYALTY_PACKAGE


def test_catalog_validates_against_scan(tmp_path):
    scan = _scan(tmp_path)
    assert validate_turret_catalog(_cat(), scan) == []
    bad = _cat()
    bad.guns[0].magazine = 250
    bad.guns[2].magazine = 50
    errs = validate_turret_catalog(bad, scan)
    assert any("ODC_TurretGun_Small: magazine 250" in e for e in errs)
    assert any("EGO_TurretGun_Small_SMG: no OE_AmmoKit turret" in e for e in errs)
    missing = TurretCatalog(guns=_cat().guns[:3])
    assert "turret gun not in catalog: OEC_TurretGun_Small" in validate_turret_catalog(missing, scan)


def test_absent_dlc_gun_skipped(tmp_path):
    scan = _scan(tmp_path, royalty=False)
    assert validate_turret_catalog(_cat(), scan) == []
    errs = validate_turret_catalog(_cat(), scan, present_packages=frozenset({ROYALTY_PACKAGE}))
    assert "OEC_TurretGun_Small: not a scanned turret gun" in errs


def test_emit_turret_buildings_and_guns(tmp_path):
    xml = emit_turret_xml(_cat(), _scan(tmp_path))
    root = ET.fromstring(xml)
    assert len(root) == 4 + 5
    assert xml.count("<thingClass>CombatExtended.Building_TurretGunCE</thingClass>") == 2 * 5
    assert '/comps/li[@Class="CompProperties_Refuelable"]' in xml
    assert "CompProperties_Explosive" not in xml
    assert 'defName="ODC_Turret_Ceiling"]/fillPercent' not in xml
    assert "<fillPercent>0.85</fillPercent>" in xml
    assert "<magazineSize>300</magazineSize>" in xml
    assert "<ammoSet>AmmoSet_OE_ODC_TurretGun_Small</ammoSet>" in xml
    assert "<recoilPattern>Mounted</recoilPattern>" in xml
    ego = xml.split("<defName>EGO_TurretGun_Small_SMG</defName>")[1].split("</Operation>")[0]
    assert "AmmoUser" not in ego
    assert f'MayRequire="{ROYALTY_PACKAGE}"' in xml


def test_ammo_net_feed_only_on_fueled_frame_turrets(tmp_path):
    xml = emit_ammo_net_xml(_cat(), _scan(tmp_path))
    ET.fromstring(xml)
    assert 'defName="ODC_Turret_Small"]/comps' in xml
    assert 'defName="ODC_Turret_Ceiling"]/comps' in xml
    assert 'defName="OEC_Turret_Small"]/comps' in xml
    assert "ODC_Turret_TacticalTurret" not in xml
    assert "EGO_Turret_Small_SMG" not in xml
    assert '<li Class="ObsidiaCEAmmoNet.CompProperties_AmmoNetFeed">' in xml
    assert "<shotsPerUnit>12</shotsPerUnit>" in xml
    assert "<shotsPerUnit>2.86</shotsPerUnit>" in xml
    assert "<pipeNet>OE_AmmoNet</pipeNet>" in xml


def _dir(env, default):
    p = Path(os.environ.get(env, default))
    return p if p.is_dir() else None


@pytest.mark.skipif(not CORE.is_dir(), reason="Obsidia Core not installed")
def test_real_turrets_fully_catalogued():
    roy = _dir("OBSIDIA_ROYALTY", DEFAULT_OBSIDIA_ROYALTY)
    bio = _dir("OBSIDIA_BIOTECH", DEFAULT_OBSIDIA_BIOTECH)
    ody = _dir("OBSIDIA_ODYSSEY", DEFAULT_OBSIDIA_ODYSSEY)
    scan = scan_turrets(CORE, roy, biotech=bio, odyssey=ody)
    present = frozenset(
        pkg for pkg, p in ((ROYALTY_PACKAGE, roy), (BIOTECH_PACKAGE, bio), (ODYSSEY_PACKAGE, ody)) if p
    )
    errs = validate_turret_catalog(load_turret_catalog(ROOT / "catalog"), scan, present_packages=present)
    assert errs == [], "\n".join(errs)
    if roy and bio and ody:
        assert len(scan.turrets) == 56
        assert len(scan.guns) == 36


def test_committed_ammo_net_is_vef_gated_and_built():
    loadfolders = (ROOT / "LoadFolders.xml").read_text(encoding="utf-8")
    assert (
        '<li IfModActive="OskarPotocki.VanillaFactionsExpanded.Core">1.7/Mods/AmmoNet</li>'
        in loadfolders
    )
    dll = ROOT / "1.7" / "Mods" / "AmmoNet" / "Assemblies" / "ObsidiaCEAmmoNet.dll"
    data = dll.read_bytes()
    for name in (b"ObsidiaCEAmmoNet", b"CompProperties_AmmoNetFeed", b"CompAmmoNetFeed"):
        assert name in data
    patch = (ROOT / "1.7" / "Mods" / "AmmoNet" / "Patches" / "OE_AmmoNetFeed.xml").read_text(
        encoding="utf-8"
    )
    assert patch.count("ObsidiaCEAmmoNet.CompProperties_AmmoNetFeed") == 40
    assert "TacticalTurret" not in patch
    # Base patch never references the bridge assembly.
    base = (ROOT / "1.7" / "Patches" / "Buildings" / "OE_Turrets.xml").read_text(encoding="utf-8")
    assert "ObsidiaCEAmmoNet" not in base
