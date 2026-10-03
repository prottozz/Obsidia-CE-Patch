from pathlib import Path

from oe_ce.load import load_catalog
from oe_ce.models import Catalog, Family, Member
from oe_ce.validate import validate_catalog


def test_duplicate_defname_is_error():
    cat = Catalog(families=[
        Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")]),
        Family("other", "rifle", "ballistic", members=[Member("OE_Rifle", "occ")]),
    ])
    errs = validate_catalog(cat, core_ranged={"OE_Rifle"})
    assert any("OE_Rifle" in e and "duplicate" in e.lower() for e in errs)


def test_missing_core_gun_is_error():
    cat = Catalog(families=[
        Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")]),
    ])
    errs = validate_catalog(cat, core_ranged={"OE_Rifle", "OCC_Rifle"})
    assert any("OCC_Rifle" in e for e in errs)


def test_pistol_explicit_emp_is_error():
    cat = Catalog(families=[
        Family("impaler", "pistol", "ballistic", cartridges=["standard", "ap", "hp", "emp"],
               members=[Member("OE_Pistol", "proto")]),
    ])
    errs = validate_catalog(cat, core_ranged={"OE_Pistol"})
    assert any("emp" in e.lower() and "pistol" in e.lower() for e in errs)


def test_rifle_missing_emp_is_error():
    cat = Catalog(families=[
        Family("cerberus", "rifle", "ballistic", cartridges=["standard", "ap", "hp"],
               members=[Member("OE_Rifle", "proto")]),
    ])
    errs = validate_catalog(cat, core_ranged={"OE_Rifle"})
    assert any("emp" in e.lower() for e in errs)


def test_load_yaml_class_field(tmp_path: Path):
    (tmp_path / "ballistic.yaml").write_text(
        "families:\n"
        "  - id: cerberus\n"
        "    type: rifle\n"
        "    class: ballistic\n"
        "    members:\n"
        "      - defName: OE_Rifle\n"
        "        rung: proto\n",
        encoding="utf-8",
    )
    cat = load_catalog(tmp_path)
    assert cat.families[0].class_name == "ballistic"
    assert cat.families[0].members[0].def_name == "OE_Rifle"
