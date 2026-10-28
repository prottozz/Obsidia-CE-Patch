import xml.etree.ElementTree as ET
from pathlib import Path

from oe_ce.emit_race_verbs import emit_race_verb_xml, race_projectile_defs, scan_race_verbs
from oe_ce.scan_obsidia import index_thingdefs

ROOT = Path(__file__).resolve().parents[2]

DEFS = """<Defs>
  <ThingDef Name="AnimalBase" Abstract="True"><race><body>Bird</body></race></ThingDef>
  <ThingDef ParentName="AnimalBase">
    <defName>OE_Bruul_Acid</defName>
    <verbs>
      <li>
        <label>acid inc</label>
        <verbClass>Verb_Shoot</verbClass>
        <defaultProjectile>Bullet_Bruul_Acid</defaultProjectile>
        <minRange>2.0</minRange>
        <range>23.9</range>
        <commonality>0.8</commonality>
      </li>
    </verbs>
  </ThingDef>
  <ThingDef ParentName="AnimalBase">
    <defName>OE_Slime_Boom</defName>
    <verbs><li><verbClass>Verb_Shoot</verbClass><defaultProjectile>Bullet_Slime_Boom</defaultProjectile></li></verbs>
  </ThingDef>
  <ThingDef ParentName="AnimalBase"><defName>OE_Bad</defName>
    <verbs><li><verbClass>Verb_Shoot</verbClass><defaultProjectile>Missing</defaultProjectile></li></verbs></ThingDef>
  <ThingDef Name="SpitterBase" ParentName="AnimalBase" Abstract="True">
    <verbs><li><verbClass>Verb_Shoot</verbClass><defaultProjectile>Bullet_Bruul_Acid</defaultProjectile></li></verbs></ThingDef>
  <ThingDef ParentName="SpitterBase"><defName>OE_Inherits</defName></ThingDef>
  <ThingDef ParentName="AnimalBase"><defName>OE_Melee</defName></ThingDef>
  <ThingDef ParentName="BaseBullet"><defName>Bullet_Bruul_Acid</defName><label>acid inc</label>
    <graphicData><texPath>Things/Projectile/Acid</texPath><graphicClass>Graphic_Single</graphicClass><drawSize>1.2</drawSize></graphicData>
    <projectile><damageDef>OTCAcid</damageDef><damageAmountBase>6</damageAmountBase><speed>65</speed></projectile></ThingDef>
  <ThingDef ParentName="BaseBullet"><defName>Bullet_Slime_Boom</defName><thingClass>Projectile_Explosive</thingClass>
    <projectile><damageDef>OTCCryo</damageDef><damageAmountBase>15</damageAmountBase><explosionRadius>1.9</explosionRadius><speed>40</speed></projectile></ThingDef>
</Defs>"""


def _scan(tmp_path, races):
    path = tmp_path / "d.xml"
    path.write_text(DEFS, encoding="utf-8")
    return scan_race_verbs(index_thingdefs([path]), races)


def test_scan_finds_ranged_verbs_and_fails_closed(tmp_path):
    entries, errors = _scan(
        tmp_path,
        {"OE_Bruul_Acid": None, "OE_Bad": None, "OE_Inherits": None, "OE_Melee": None, "OE_Gone": None},
    )
    assert [e.race for e in entries] == ["OE_Bruul_Acid"]
    assert any("OE_Bad" in e and "Missing" in e for e in errors)
    assert any("OE_Inherits" in e and "inherited" in e for e in errors)


def test_ink_is_blunt_plus_element_and_verb_is_ce(tmp_path):
    entries, _ = _scan(tmp_path, {"OE_Bruul_Acid": None, "OE_Slime_Boom": "Some.Package"})
    defs = {el.findtext("defName"): el for el in ET.fromstring("<Defs>" + "".join(race_projectile_defs(entries)) + "</Defs>")}
    ink = defs["Bullet_OE_Bruul_Acid_CE"]
    assert ink.get("ParentName") == "BaseBulletCE"
    assert ink.findtext("projectile/damageDef") == "Blunt"
    assert ink.findtext("projectile/damageAmountBase") == "6"
    assert ink.findtext("projectile/armorPenetrationBlunt") == "6"
    assert ink.findtext("projectile/secondaryDamage/li/def") == "OTCAcid"
    assert ink.findtext("projectile/secondaryDamage/li/amount") == "6"
    assert ink.findtext("projectile/speed") == "65"
    assert ink.findtext("graphicData/texPath") == "Things/Projectile/Acid"
    boom = defs["Bullet_OE_Slime_Boom_CE"]
    assert boom.findtext("thingClass") == "CombatExtended.ProjectileCE_Explosive"
    assert boom.findtext("projectile/explosionRadius") == "1.3"
    xml = emit_race_verb_xml(entries)
    root = ET.fromstring(xml)
    assert len(root) == 2
    assert 'MayRequire="Some.Package"' in xml
    acid = xml.split('defName="OE_Bruul_Acid"]/verbs')[1].split("</Operation>")[0]
    assert "<verbClass>CombatExtended.Verb_ShootCE</verbClass>" in acid
    assert "<defaultProjectile>Bullet_OE_Bruul_Acid_CE</defaultProjectile>" in acid
    assert "<minRange>2.0</minRange>" in acid and "<range>23.9</range>" in acid
    assert "Bullet_Bruul_Acid<" not in acid


def test_committed_bruul_ink():
    patch = (ROOT / "1.7" / "Patches" / "Races" / "OE_RaceVerbs.xml").read_text(encoding="utf-8")
    for el in ("Acid", "Cryo", "EMP", "Fire"):
        assert f'defName="OE_Bruul_{el}"]/verbs' in patch
        assert f"<defaultProjectile>Bullet_OE_Bruul_{el}_CE</defaultProjectile>" in patch
    assert patch.count("CombatExtended.Verb_ShootCE") == 4
    ammo = ET.parse(ROOT / "1.7" / "Defs" / "Ammo" / "OE_Ammo.xml").getroot()
    ink = {el.findtext("defName"): el for el in ammo if (el.findtext("defName") or "").startswith("Bullet_OE_Bruul_")}
    assert len(ink) == 4
    elements = {name: el.findtext("projectile/secondaryDamage/li/def") for name, el in ink.items()}
    assert elements == {
        "Bullet_OE_Bruul_Acid_CE": "OTCAcid",
        "Bullet_OE_Bruul_Cryo_CE": "OTCCryo",
        "Bullet_OE_Bruul_EMP_CE": "EMP",
        "Bullet_OE_Bruul_Fire_CE": "Flame",
    }
    assert ink["Bullet_OE_Bruul_EMP_CE"].findtext("projectile/empShieldBreakChance") == "0.15"
    assert ink["Bullet_OE_Bruul_Fire_CE"].findtext("projectile/ai_IsIncendiary") == "true"
