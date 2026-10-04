from oe_ce.emit_recipes import emit_recipe_xml
from oe_ce.models import Family, Member


def test_recipes_use_obsidia_bench_and_mats():
    fam = Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")])
    xml = emit_recipe_xml([fam])
    assert "OE_WeaponWorkbench" in xml
    assert "OE_Obsidian" in xml
    assert "OE_AmmoKit" in xml
    assert "TableMachining" not in xml
    assert "MakeAmmo_OE_cerberus_ballistic_standard_small" in xml
    assert "MakeAmmo_OE_cerberus_ballistic_standard_large" in xml
    assert "<workAmount>2000</workAmount>" in xml
    assert "<workAmount>5000</workAmount>" in xml
