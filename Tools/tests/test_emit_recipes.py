from oe_ce.emit_recipes import emit_recipe_xml
from oe_ce.models import Family, Member


def test_recipes_use_obsidia_bench_and_mats():
    fam = Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")])
    xml = emit_recipe_xml([fam])
    assert "OE_WeaponWorkbench" in xml
    assert "OE_Obsidian" in xml
    assert "OE_AmmoKit" in xml
    assert "TableMachining" not in xml
    assert "MakeAmmo_OE_rifle_ballistic_standard_small" in xml
    assert "MakeAmmo_OE_rifle_ballistic_standard_large" in xml
    assert "<workAmount>2000</workAmount>" in xml
    assert "<workAmount>5000</workAmount>" in xml
    assert "<workSkill>Crafting</workSkill>" in xml
    assert "<workSpeedStat>SmithingSpeed</workSpeedStat>" in xml
    assert "<workSkillLearnFactor>0.5</workSkillLearnFactor>" in xml
    assert 'ParentName="AmmoRecipeBase"' in xml


def test_shared_caliber_emits_one_recipe_pair():
    xml = emit_recipe_xml(
        [
            Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")]),
            Family("unchained", "minigun", "ballistic", members=[Member("OEC_Minigun", "oec")]),
        ]
    )
    assert xml.count("MakeAmmo_OE_rifle_ballistic_standard_small") == 1
    assert "MakeAmmo_OE_cerberus" not in xml


def test_elemental_recipes_emit_one_cartridge_pair():
    xml = emit_recipe_xml(
        [Family("nova", "sniper", "fire", members=[Member("OTC_SniperRifle_Fire", "otc")])]
    )
    assert "MakeAmmo_OE_rifle_fire_fire_small" in xml
    assert "MakeAmmo_OE_rifle_fire_fire_large" in xml
    assert "MakeAmmo_OE_rifle_fire_standard" not in xml


def test_experimental_recipe_labels_are_readable():
    xml = emit_recipe_xml(
        [
            Family(
                "dark_hydra",
                "minigun",
                "ballistic",
                experimental=True,
                members=[Member("OE_DarkCrusader_Minigun", "proto")],
            )
        ]
    )
    assert "<label>make OE dark hydra ballistic standard x200</label>" in xml
    assert "make OE exp_dark_hydra" not in xml
    assert "MakeAmmo_OE_exp_dark_hydra_ballistic_standard_small" in xml
