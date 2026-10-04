import os
from pathlib import Path

from oe_ce.constants import DEFAULT_OBSIDIA_CORE
from oe_ce.scan_obsidia import scan_core_ranged, weapon_projectile_graphic

CORE = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))


def test_scan_finds_proto_cerberus():
    names = scan_core_ranged(CORE)
    assert "OE_Rifle" in names
    assert "OCC_Rifle" in names
    assert "Bullet_OE_R" not in names


def test_weapon_projectile_graphic_walks_parent(tmp_path):
    weapons = tmp_path / "Defs" / "ThingDefs_Misc" / "Weapons"
    weapons.mkdir(parents=True)
    (weapons / "Guns.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef Name="ODCElemRevolverBullet" Abstract="True">
    <graphicData>
      <texPath>Things/Projectile/ODC_BulletSmall</texPath>
      <graphicClass>Graphic_Single</graphicClass>
    </graphicData>
  </ThingDef>
  <ThingDef ParentName="ODCElemRevolverBullet">
    <defName>Bullet_ODC_R_Fire</defName>
  </ThingDef>
  <ThingDef>
    <defName>ODC_Revolver_Fire</defName>
    <verbs>
      <li>
        <defaultProjectile>Bullet_ODC_R_Fire</defaultProjectile>
      </li>
    </verbs>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    graphic = weapon_projectile_graphic(tmp_path, "ODC_Revolver_Fire")
    assert graphic is not None
    assert graphic.tex_path == "Things/Projectile/ODC_BulletSmall"
    assert graphic.graphic_class == "Graphic_Single"


def test_weapon_projectile_graphic_walks_gun_parent_verbs(tmp_path):
    weapons = tmp_path / "Defs" / "ThingDefs_Misc" / "Weapons"
    weapons.mkdir(parents=True)
    (weapons / "Guns.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef Name="CACPistolBase" Abstract="True">
    <verbs>
      <li>
        <defaultProjectile>Bullet_CAC_P</defaultProjectile>
      </li>
    </verbs>
  </ThingDef>
  <ThingDef ParentName="CACPistolBase">
    <defName>CAC_Pistol</defName>
  </ThingDef>
  <ThingDef>
    <defName>Bullet_CAC_P</defName>
    <graphicData>
      <texPath>Things/Projectile/CAC_BulletSmall</texPath>
      <graphicClass>Graphic_Single</graphicClass>
    </graphicData>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    graphic = weapon_projectile_graphic(tmp_path, "CAC_Pistol")
    assert graphic is not None
    assert graphic.tex_path == "Things/Projectile/CAC_BulletSmall"
