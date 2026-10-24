from oe_ce.emit_grenade_belts import GRENADE_BELTS, emit_grenade_belt_xml


def test_emit_converts_all_seven_belts_to_ce_throw_verb():
    xml = emit_grenade_belt_xml()
    assert len(GRENADE_BELTS) == 7
    assert "forcedMissRadius" not in xml
    assert "Verb_LaunchProjectileStaticCE" in xml
    assert 'Class="CombatExtended.VerbPropertiesCE"' in xml
    assert "CombatExtended.ProjectilePropertiesCE" in xml
    for def_name, projectile, _label, _range in GRENADE_BELTS:
        assert f'defName="{def_name}"' in xml
        assert f"<defaultProjectile>{projectile}</defaultProjectile>" in xml
    assert xml.count('MayRequire=') == 0
    inner = xml.split("<operations>")[1].split("</operations>")[0]
    assert "<li Class=" in inner
    assert "<Operation Class=" not in inner


def test_omg_keeps_longer_range():
    xml = emit_grenade_belt_xml()
    assert xml.count("<range>17.9</range>") == 1
    assert xml.count("<range>15.9</range>") == 6
    assert 'defName="OMG_GrenadeBelt"]/verbs</xpath>' in xml
