from pathlib import Path

from oe_ce.emit_guns import emit_gun_patches
from oe_ce.models import Family, Member


def _minimal_core(tmp_path: Path, *, with_tools: bool) -> Path:
    weapons = tmp_path / "Defs" / "ThingDefs_Misc" / "Weapons"
    weapons.mkdir(parents=True)
    tools_block = "    <tools><li /></tools>\n" if with_tools else ""
    (weapons / "Guns.xml").write_text(
        f"""<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef>
    <defName>OE_Rifle</defName>
    <verbs><li /></verbs>
{tools_block}  </ThingDef>
  <ThingDef>
    <defName>OCC_Rifle</defName>
    <verbs><li /></verbs>
{tools_block}  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    return tmp_path


def test_shared_ammoset_different_stats(tmp_path):
    fam = Family(
        "cerberus",
        "rifle",
        "ballistic",
        members=[
            Member("OE_Rifle", "proto"),
            Member("OCC_Rifle", "occ"),
        ],
    )
    core = _minimal_core(tmp_path, with_tools=True)
    xml = emit_gun_patches([fam], core)
    assert xml.count("AmmoSet_OE_OE_Rifle") == 1
    assert xml.count("AmmoSet_OE_OCC_Rifle") == 1
    assert "<defaultProjectile>Bullet_OE_OE_Rifle_standard</defaultProjectile>" in xml
    assert "<defaultProjectile>Bullet_OE_OCC_Rifle_standard</defaultProjectile>" in xml
    assert "<defName>OE_Rifle</defName>" in xml
    assert "<defName>OCC_Rifle</defName>" in xml
    assert "PatchOperationMakeGunCECompatible" in xml
    assert "<range>55</range>" in xml
    assert "<range>48</range>" in xml
    assert "PatchOperationReplace" in xml


def test_tools_replace_skipped_without_core_tools(tmp_path):
    fam = Family(
        "cerberus",
        "rifle",
        "ballistic",
        members=[Member("OE_Rifle", "proto")],
    )
    core = _minimal_core(tmp_path, with_tools=False)
    xml = emit_gun_patches([fam], core)
    assert "PatchOperationReplace" not in xml


def test_elemental_gun_uses_single_class_projectile(tmp_path):
    fam = Family(
        "nova",
        "sniper",
        "fire",
        members=[Member("OTC_SniperRifle_Fire", "otc")],
    )
    weapons = tmp_path / "Defs" / "ThingDefs_Misc" / "Weapons"
    weapons.mkdir(parents=True)
    (weapons / "Guns.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef>
    <defName>OTC_SniperRifle_Fire</defName>
    <verbs><li /></verbs>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    xml = emit_gun_patches([fam], tmp_path)
    assert "<defaultProjectile>Bullet_OE_OTC_SniperRifle_Fire_fire</defaultProjectile>" in xml
    assert "Bullet_OE_rifle_fire_standard" not in xml
    assert "<ammoSet>AmmoSet_OE_OTC_SniperRifle_Fire</ammoSet>" in xml
