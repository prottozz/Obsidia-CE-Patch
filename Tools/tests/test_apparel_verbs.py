import xml.etree.ElementTree as ET
from pathlib import Path

from oe_ce.constants import ANOMALY_PACKAGE, BIOTECH_PACKAGE, ODYSSEY_PACKAGE
from oe_ce.emit_apparel_verbs import emit_apparel_verb_xml
from oe_ce.scan_apparel_verbs import FLARE, GAS, TURRET, scan_apparel_verbs

CORE = """
  <ThingDef Name="OEArmorBase" Abstract="True">
    <apparel><layers><li>Middle</li><li>Shell</li></layers></apparel>
  </ThingDef>
  <ThingDef Name="OEHelmetBase" Abstract="True">
    <apparel><layers><li>Overhead</li></layers></apparel>
  </ThingDef>
  <ThingDef Name="OTCArmorMod" ParentName="OEArmorBase">
    <defName>OTC_Armor_M</defName>
  </ThingDef>
  <ThingDef ParentName="OEArmorBase">
    <defName>OTC_Armor_M_Grenadier_Acid</defName>
    <verbs><li><verbClass>Verb_LaunchProjectileStatic</verbClass><defaultProjectile>Grenade_Armor_OTC_Acid</defaultProjectile></li></verbs>
  </ThingDef>
"""

ANOMALY = """
  <ThingDef ParentName="OTCArmorMod">
    <defName>OTC_Armor_M_Turret</defName>
    <verbs>
      <li>
        <verbClass>Verb_LaunchProjectileStatic</verbClass>
        <label>deploy acid turret</label>
        <defaultProjectile>Grenade_Armor_OTC_TurretPack_Acid</defaultProjectile>
        <range>22.9</range>
        <targetParams>
          <canTargetLocations>true</canTargetLocations>
        </targetParams>
      </li>
      <li>
        <verbClass>Verb_LaunchProjectileStatic</verbClass>
        <label>deploy fire turret</label>
        <defaultProjectile>Grenade_Armor_OTC_TurretPack_Fire</defaultProjectile>
      </li>
    </verbs>
  </ThingDef>
  <ThingDef ParentName="BaseGrenadeProjectile">
    <defName>Grenade_Armor_OTC_TurretPack_Acid</defName>
    <thingClass>Projectile_SpawnsThing</thingClass>
    <projectile><speed>45</speed><explosionRadius>15.9</explosionRadius><spawnsThingDef>OTC_Turret_TacticalTurret_Acid</spawnsThingDef></projectile>
  </ThingDef>
  <ThingDef ParentName="BaseGrenadeProjectile">
    <defName>Grenade_Armor_OTC_TurretPack_Fire</defName>
    <thingClass>Projectile_SpawnsThing</thingClass>
    <projectile><spawnsThingDef>OTC_Turret_TacticalTurret_Fire</spawnsThingDef></projectile>
  </ThingDef>
  <ThingDef ParentName="OEArmorBase">
    <defName>CAC_PriestArmor</defName>
    <verbs><li><verbClass>Verb_LaunchProjectileStaticPsychic</verbClass><defaultProjectile>Grenade_DisruptorFlare</defaultProjectile><violent>false</violent></li></verbs>
  </ThingDef>
  <ThingDef ParentName="OEHelmetBase">
    <defName>OMG_Trophy_Helmet_Firemark</defName>
    <verbs><li><verbClass>Verb_LaunchProjectileStaticPsychic</verbClass><defaultProjectile>OMG_DisruptorFlare</defaultProjectile></li></verbs>
  </ThingDef>
  <ThingDef ParentName="BaseBullet">
    <defName>OMG_DisruptorFlare</defName>
    <thingClass>Projectile_SpawnsThing</thingClass>
    <projectile><speed>65</speed><spinRate>3</spinRate><explosionRadius>7.9</explosionRadius><landedEffecter>DisruptorFlareLanded</landedEffecter><spawnsThingDef>DisruptorFlare</spawnsThingDef></projectile>
  </ThingDef>
  <ThingDef ParentName="OEHelmetBase">
    <defName>OMG_Trophy_Helmet_Necrospark</defName>
    <verbs><li><verbClass>Verb_LaunchProjectileStatic</verbClass><defaultProjectile>Grenade_OMG_Deadlife</defaultProjectile></li></verbs>
  </ThingDef>
  <ThingDef ParentName="BaseBullet">
    <defName>Grenade_OMG_Deadlife</defName>
    <thingClass>Projectile_Explosive</thingClass>
    <projectile><damageDef>DeadlifeDust</damageDef><speed>45</speed><explosionRadius>0.1</explosionRadius><soundExplode>ToxicShellLanded</soundExplode><postExplosionSpawnThingDef>Shell_OMG_Deadlife</postExplosionSpawnThingDef></projectile>
  </ThingDef>
"""

ODYSSEY = """
  <ThingDef ParentName="OEArmorBase">
    <defName>OMG_Armor_Swarmling</defName>
    <verbs><li><verbClass>Verb_LaunchProjectileStatic</verbClass><defaultProjectile>Grenade_Armor_OMG_SwarmlingPack</defaultProjectile></li></verbs>
  </ThingDef>
"""

BIOTECH_UNKNOWN = """
  <ThingDef ParentName="OEArmorBase">
    <defName>EGO_Armor_Shell_Gadget</defName>
    <verbs><li><verbClass>Verb_LaunchProjectileStatic</verbClass><defaultProjectile>Bullet_Mystery</defaultProjectile></li></verbs>
  </ThingDef>
  <ThingDef ParentName="BaseBullet">
    <defName>Bullet_Mystery</defName>
    <projectile><damageDef>Stun</damageDef></projectile>
  </ThingDef>
"""


def _tree(root: Path, body: str) -> Path:
    apparel = root / "Defs" / "ThingDefs_Misc" / "Apparel"
    apparel.mkdir(parents=True)
    (apparel / "F.xml").write_text(f"<Defs>{body}</Defs>", encoding="utf-8")
    return root


def _scan(tmp_path, biotech_body=None):
    core = _tree(tmp_path / "core", CORE)
    anomaly = _tree(tmp_path / "anomaly", ANOMALY)
    odyssey = _tree(tmp_path / "odyssey", ODYSSEY)
    bio = _tree(tmp_path / "bio", biotech_body) if biotech_body else None
    return scan_apparel_verbs(core, biotech=bio, anomaly=anomaly, odyssey=odyssey)


def test_scan_classifies_dlc_deploy_verbs_only(tmp_path):
    scan = _scan(tmp_path)
    assert scan.errors == []
    assert set(scan.apparel) == {
        "OTC_Armor_M_Turret",
        "CAC_PriestArmor",
        "OMG_Trophy_Helmet_Firemark",
        "OMG_Trophy_Helmet_Necrospark",
    }
    assert len(scan.apparel["OTC_Armor_M_Turret"].verbs) == 2
    assert scan.apparel["OTC_Armor_M_Turret"].package == ANOMALY_PACKAGE
    kinds = {name: p.kind for name, p in scan.projectiles.items()}
    assert kinds == {
        "Grenade_Armor_OTC_TurretPack_Acid": TURRET,
        "Grenade_Armor_OTC_TurretPack_Fire": TURRET,
        "OMG_DisruptorFlare": FLARE,
        "Grenade_OMG_Deadlife": GAS,
    }
    # Vanilla flare is CE-patched by CE itself; Core grenadiers and Swarmling stay vanilla.
    assert "Grenade_DisruptorFlare" not in scan.projectiles
    assert "OTC_Armor_M_Grenadier_Acid" not in scan.apparel
    assert "OMG_Armor_Swarmling" not in scan.apparel


def test_unknown_dlc_deploy_verb_fails_closed(tmp_path):
    scan = _scan(tmp_path, BIOTECH_UNKNOWN)
    assert any("EGO_Armor_Shell_Gadget" in e and "Bullet_Mystery" in e for e in scan.errors)


def test_emit_converts_verbs_and_projectiles(tmp_path):
    xml = emit_apparel_verb_xml(_scan(tmp_path))
    root = ET.fromstring(xml)
    assert all(op.get("MayRequire") == ANOMALY_PACKAGE for op in root)
    assert "Verb_LaunchProjectileStatic<" not in xml
    assert "Verb_LaunchProjectileStaticPsychic" not in xml
    assert "Verb_ShootCEOneUse" not in xml
    assert xml.count("<verbClass>CombatExtended.Verb_LaunchProjectileStaticCE</verbClass>") == 5
    assert "<label>deploy acid turret</label>" in xml
    assert "<range>22.9</range>" in xml
    assert "<canTargetLocations>true</canTargetLocations>" in xml
    assert "<thingClass>CombatExtended.ProjectileCE_SpawnsThing</thingClass>" in xml
    assert "<spawnsThingDef>OTC_Turret_TacticalTurret_Acid</spawnsThingDef>" in xml
    assert "<spawnsThingDef>DisruptorFlare</spawnsThingDef>" in xml
    assert "<landedEffecter>DisruptorFlareLanded</landedEffecter>" in xml
    assert "<thingClass>CombatExtended.ProjectileCE_Explosive</thingClass>" in xml
    assert "<postExplosionSpawnThingDef>Shell_OMG_Deadlife</postExplosionSpawnThingDef>" in xml
    assert "<damageAmountBase>0</damageAmountBase>" in xml
    assert "<speed>45</speed>" not in xml
    assert 'defName="Grenade_DisruptorFlare"' not in xml
