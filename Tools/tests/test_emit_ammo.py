from oe_ce.emit_ammo import EMP_DEDICATED_AMOUNT, EMP_SIDE_AMOUNT, emit_ammo_xml
from oe_ce.models import Family, Member


def test_cerberus_set_and_emp_weaker_than_dedicated():
    cerb = Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")])
    quasar = Family("quasar", "rifle", "emp", members=[Member("OTC_Rifle_EMP", "otc")])
    xml = emit_ammo_xml([cerb, quasar])
    assert "AmmoSet_OE_OE_Rifle" in xml
    assert "Ammo_OE_rifle_ballistic_emp" in xml
    assert "Ammo_OE_rifle_ballistic_standard" in xml
    assert EMP_DEDICATED_AMOUNT > EMP_SIDE_AMOUNT
    assert f"<amount>{EMP_SIDE_AMOUNT}</amount>" in xml
    assert f"<amount>{EMP_DEDICATED_AMOUNT}</amount>" in xml
    assert "CE_AutoEnableCrafting_TableMachining" not in xml
    assert "<label>rifle ballistic standard</label>" in xml
    assert "AmmoOE_rifle_ballistic" in xml
    assert "<thingCategories>" in xml
    assert "<li>AmmoOE_rifle_ballistic</li>" in xml


def test_standard_ammo_class_is_full_metal_jacket():
    """CE GizmoAmmoStatus reads ammoClass.LabelCap; defName is FullMetalJacket, not FMJ."""
    xml = emit_ammo_xml(
        [Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")])]
    )
    assert "<ammoClass>FullMetalJacket</ammoClass>" in xml
    assert "<ammoClass>FMJ</ammoClass>" not in xml
    assert "<ammoClass>ArmorPiercing</ammoClass>" in xml
    assert "<ammoClass>HollowPoint</ammoClass>" in xml
    assert "<ammoClass>Ionized</ammoClass>" in xml


def test_ammo_mass_and_bulk_are_ce_small_round():
    xml = emit_ammo_xml(
        [Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")])]
    )
    assert "<Mass>0.01</Mass>" in xml
    assert "<Bulk>0.01</Bulk>" in xml


def test_bullets_have_graphic_and_speed():
    xml = emit_ammo_xml(
        [Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")])]
    )
    assert "<texPath>Things/Projectile/Charged/ChargeShot</texPath>" in xml
    assert "<graphicClass>Graphic_Single</graphicClass>" in xml
    assert "<speed>151</speed>" in xml


def test_rifle_and_minigun_emit_one_shared_ammo_set():
    xml = emit_ammo_xml(
        [
            Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")]),
            Family("unchained", "minigun", "ballistic", members=[Member("OEC_Minigun", "oec")]),
        ]
    )
    assert xml.count("<defName>Ammo_OE_rifle_ballistic_standard</defName>") == 1
    assert "<defName>AmmoSet_OE_OE_Rifle</defName>" in xml
    assert "<defName>AmmoSet_OE_OEC_Minigun</defName>" in xml
    assert "AmmoSet_OE_cerberus" not in xml
    assert "AmmoSet_OE_unchained" not in xml
    assert "<label>rifle ballistic standard</label>" in xml
    assert "Bullet_OE_OE_Rifle_standard" in xml
    assert "Bullet_OE_OEC_Minigun_standard" in xml


def test_elemental_ammo_is_single_cartridge_with_class_effect():
    fire = Family("nova", "sniper", "fire", members=[Member("OTC_SniperRifle_Fire", "otc")])
    acid = Family("celestial", "pistol", "acid", members=[Member("OTC_Pistol_Acid", "otc")])
    emp = Family("quasar", "rifle", "emp", members=[Member("OTC_Rifle_EMP", "otc")])
    xml = emit_ammo_xml([fire, acid, emp])
    assert "<defName>Ammo_OE_rifle_fire_fire</defName>" in xml
    assert "Ammo_OE_rifle_fire_standard" not in xml
    assert "Ammo_OE_rifle_fire_ap" not in xml
    assert "<def>Flame</def>" in xml
    assert "<ai_IsIncendiary>true</ai_IsIncendiary>" in xml
    assert "<def>OTCAcid</def>" in xml
    acid_sharp = xml.split("<defName>Bullet_OE_OTC_Pistol_Acid_acid</defName>", 1)[1]
    acid_sharp = acid_sharp.split("</ThingDef>", 1)[0]
    assert "<armorPenetrationSharp>40</armorPenetrationSharp>" in acid_sharp
    ballistic = emit_ammo_xml(
        [Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")])]
    )
    standard = ballistic.split("<defName>Bullet_OE_OE_Rifle_standard</defName>", 1)[1]
    standard = standard.split("</ThingDef>", 1)[0]
    assert "<armorPenetrationSharp>18</armorPenetrationSharp>" in standard
    assert xml.count("<defName>Ammo_OE_rifle_emp_emp</defName>") == 1
    assert "Ammo_OE_rifle_emp_standard" not in xml
    assert f"<amount>{EMP_DEDICATED_AMOUNT}</amount>" in xml
    assert "<ammoClass>OE_Fire</ammoClass>" in xml
    assert "<ammoClass>OE_Acid</ammoClass>" in xml
    assert "<ammoClass>Ionized</ammoClass>" in xml
    assert "<label>rifle fire</label>" in xml


def test_experimental_ammo_label_omits_exp_prefix():
    xml = emit_ammo_xml(
        [
            Family(
                "dark_giants_bane",
                "rocket",
                "ballistic",
                experimental=True,
                members=[Member("OE_DarkCrusader_RocketLauncher", "proto")],
            )
        ]
    )
    assert "<label>dark giants bane ballistic standard</label>" in xml
    assert "<label>exp_dark_giants_bane" not in xml
    assert "Ammo_OE_exp_dark_giants_bane_ballistic_standard" in xml


def test_member_bullets_use_core_projectile_graphic(tmp_path):
    weapons = tmp_path / "Defs" / "ThingDefs_Misc" / "Weapons"
    weapons.mkdir(parents=True)
    (weapons / "Bows.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef Name="OEArrowBase" Abstract="True">
    <graphicData>
      <texPath>Things/Projectile/OE_Arrow</texPath>
      <graphicClass>Graphic_Single</graphicClass>
      <drawSize>0.8</drawSize>
    </graphicData>
  </ThingDef>
  <ThingDef ParentName="OEArrowBase">
    <defName>Arrow_OE</defName>
  </ThingDef>
  <ThingDef>
    <defName>OE_Bow</defName>
    <verbs>
      <li>
        <defaultProjectile>Arrow_OE</defaultProjectile>
      </li>
    </verbs>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    xml = emit_ammo_xml(
        [Family("nimbus", "bow", "ballistic", members=[Member("OE_Bow", "proto")])],
        core=tmp_path,
    )
    assert "<defName>AmmoSet_OE_OE_Bow</defName>" in xml
    assert "<defName>Ammo_OE_bow_ballistic_standard</defName>" in xml
    assert "<defName>Bullet_OE_OE_Bow_standard</defName>" in xml
    bow = xml.split("<defName>Bullet_OE_OE_Bow_standard</defName>", 1)[1]
    bow = bow.split("</ThingDef>", 1)[0]
    assert "<texPath>Things/Projectile/OE_Arrow</texPath>" in bow
    assert "<drawSize>0.8</drawSize>" in bow
    assert "ChargeShot" not in bow
