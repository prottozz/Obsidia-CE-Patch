import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from oe_ce.emit_ammo import emit_ammo_xml
from oe_ce.emit_guns import emit_gun_patches
from oe_ce.explosive import Blast, explosive_round, min_range, projectile_blast
from oe_ce.models import Family, Member
from oe_ce.scan_obsidia import index_thingdefs

ROOT = Path(__file__).resolve().parents[2]

OCC = Blast("OCCBlast", 16, 1.9, "Projectile_Explosive")
OCC_M = Blast("OCCBlast", 18, 1.9, "Projectile_Explosive")
ROCKET_M = Blast("OCCBlast", 50, 4.9, "Projectile_Explosive")
ODC_RL = Blast("OCCBlast", 20, 4.9, "Projectile_Explosive")
OMC_RL = Blast("OCCBlast", 30, 3.9, "Projectile_Explosive")
DARK = Blast("OCCBlast", 8, 1.9, "Projectile_Explosive")
BOW = Blast("OCCBlast", 20, 2.9, "Projectile_Explosive")
GL_FIRE = Blast("Flame", 35, 2.9, "Projectile_Explosive")
TURRET_BIG = Blast("OCCBlast", 60, 4.9, "Projectile_Explosive")
DOOMSDAY = Blast("Bomb", None, 9.9, "Projectile_DoomsdayRocket")


@pytest.mark.parametrize(
    "blast,wtype,expected",
    [
        (OCC, "rifle", (1.3, 22, 0)),
        (OCC_M, "minigun", (1.3, 25, 0)),
        (BOW, "bow", (2.0, 60, 20)),
        (ROCKET_M, "rocket", (3.4, 150, 30)),
        (ODC_RL, "rocket", (3.4, 60, 30)),
        (OMC_RL, "rocket", (2.7, 90, 30)),
        (DARK, "rocket", (1.3, 11, 0)),
        (GL_FIRE, "launcher", (2.0, 35, 0)),
        (TURRET_BIG, "launcher", (3.4, 180, 20)),
        (DOOMSDAY, "rocket", (6.0, 150, 40)),
    ],
)
def test_spec_example_table(blast, wtype, expected):
    rnd = explosive_round(blast, wtype, "standard")
    assert (rnd.radius, rnd.damage, rnd.fragments) == expected


def test_cartridge_shaping_and_speed():
    ap = explosive_round(OCC, "rifle", "ap")
    hp = explosive_round(ROCKET_M, "rocket", "hp")
    emp = explosive_round(OCC, "rifle", "emp")
    assert (ap.radius, ap.damage) == (0.7, 20)
    assert hp.radius == 3.5  # capped
    assert hp.speed == 40 and ap.speed == 151
    assert emp.damage_def == "EMP" and emp.fragments == 0
    assert min_range(OCC) is None
    assert min_range(ROCKET_M) == 5
    assert min_range(DOOMSDAY) == 7


def test_fragments_stay_near_the_blast():
    from oe_ce.explosive import frag_speed_factor

    # distance ~ 35 * f^2 cells: rocket 3.4 -> ~8.4, bow 2.0 -> ~5, doomsday 6 -> ~15
    assert frag_speed_factor(3.4) == 0.49
    assert frag_speed_factor(2.0) == 0.38
    assert frag_speed_factor(6.0) == 0.65
    assert explosive_round(ODC_RL, "rocket", "standard").frag_speed == 0.49


def _index(tmp_path):
    xml = """<Defs>
  <ThingDef Name="BaseBullet" Abstract="True"><projectile><speed>50</speed></projectile></ThingDef>
  <ThingDef ParentName="BaseBullet"><defName>Rocket</defName><thingClass>Projectile_Explosive</thingClass>
    <projectile><damageDef>OCCBlast</damageDef><damageAmountBase>40</damageAmountBase><explosionRadius>4.9</explosionRadius></projectile></ThingDef>
  <ThingDef ParentName="BaseBullet"><defName>Shell</defName><thingClass>Projectile_DoomsdayRocket</thingClass>
    <projectile><damageDef>Bomb</damageDef><explosionRadius>9.9</explosionRadius></projectile></ThingDef>
  <ThingDef ParentName="BaseBullet"><defName>Plain</defName><projectile><damageDef>Bullet</damageDef><damageAmountBase>15</damageAmountBase></projectile></ThingDef>
  <ThingDef Name="GunBase" Abstract="True"><verbs><li><defaultProjectile>Rocket</defaultProjectile></li></verbs></ThingDef>
  <ThingDef ParentName="GunBase"><defName>RL</defName></ThingDef>
  <ThingDef><defName>Arty</defName><verbs><li><defaultProjectile>Shell</defaultProjectile></li></verbs></ThingDef>
  <ThingDef><defName>MultiCannon</defName><verbs><li><defaultProjectile>Plain</defaultProjectile></li></verbs></ThingDef>
</Defs>"""
    path = tmp_path / "d.xml"
    path.write_text(xml, encoding="utf-8")
    return index_thingdefs([path])


def test_projectile_blast_scan(tmp_path):
    idx = _index(tmp_path)
    assert projectile_blast(idx, "RL") == Blast("OCCBlast", 40.0, 4.9, "Projectile_Explosive")
    arty = projectile_blast(idx, "Arty")
    assert arty.amount is None and arty.is_doomsday
    assert projectile_blast(idx, "MultiCannon") is None
    assert projectile_blast(idx, "Missing") is None


def test_emit_explosive_and_plain_bullets_with_min_range(tmp_path):
    (tmp_path / "Defs" / "ThingDefs_Misc" / "Weapons").mkdir(parents=True)
    rifle = Family("cerberus", "rifle", "ballistic", members=[Member("OCC_Rifle", "occ")])
    rocket = Family("behemoth", "rocket", "ballistic", members=[Member("OCC_RocketLauncher_M", "occ_reforge")])
    cannon = Family("pulsar", "launcher", "fire", members=[Member("OTC_MultiCannon_Fire", "otc")])
    blasts = {"OCC_Rifle": OCC, "OCC_RocketLauncher_M": ROCKET_M}
    xml = emit_ammo_xml([rifle, rocket, cannon], blasts=blasts)
    by_name = {el.findtext("defName"): el for el in ET.fromstring(xml)}
    std = by_name["Bullet_OE_OCC_Rifle_standard"]
    assert std.get("ParentName") == "BaseExplosiveBullet"
    assert std.findtext("thingClass") == "CombatExtended.ProjectileCE_Explosive"
    assert std.findtext("projectile/damageDef") == "OCCBlast"
    assert std.findtext("projectile/explosionRadius") == "1.3"
    assert std.find("projectile/applyDamageToExplosionCellsNeighbors") is not None
    assert by_name["Bullet_OE_OCC_Rifle_ap"].findtext("projectile/explosionRadius") == "0.7"
    rl = by_name["Bullet_OE_OCC_RocketLauncher_M_standard"]
    assert rl.findtext("comps/li/fragments/Fragment_Small") == "30"
    assert rl.findtext("projectile/speed") == "40"
    assert rl.findtext("comps/li/fragSpeedFactor") == "0.49"
    plain = by_name["Bullet_OE_OTC_MultiCannon_Fire_fire"]
    assert plain.get("ParentName") == "BaseBulletCE"
    guns = emit_gun_patches([rifle, rocket], tmp_path, blasts)
    rl_op = guns.split("<defName>OCC_RocketLauncher_M</defName>")[1].split("</Operation>")[0]
    assert "<minRange>5</minRange>" in rl_op
    assert "<ai_IsBuildingDestroyer>true</ai_IsBuildingDestroyer>" in rl_op
    rifle_op = guns.split("<defName>OCC_Rifle</defName>")[1].split("</Operation>")[0]
    assert "minRange" not in rifle_op


def test_committed_ammo_has_explosive_rounds_and_keeps_names():
    root = ET.parse(ROOT / "1.7" / "Defs" / "Ammo" / "OE_Ammo.xml").getroot()
    explosive = [el for el in root if el.get("ParentName") == "BaseExplosiveBullet"]
    guns = {el.findtext("defName").rsplit("_", 1)[0] for el in explosive}
    assert len(guns) == 49
    names = {el.findtext("defName") for el in explosive}
    for name in (
        "Bullet_OE_OCC_Rifle_standard",
        "Bullet_OE_OCC_RocketLauncher_M_standard",
        "Bullet_OE_ODC_TurretGun_Big_standard",
        "Bullet_OE_OTC_GrenadeLauncher_Cryo_cryo",
        "Bullet_OE_EGO_TurretGun_Small_GrenadeLauncher_cryo",
    ):
        assert name in names, name
    plain = {el.findtext("defName") for el in root if el.get("ParentName") == "BaseBulletCE"}
    assert "Bullet_OE_OTC_MultiCannon_Acid_acid" in plain
    assert "Bullet_OE_ODC_Trophy_BladeLauncher_A_standard" in plain
