# Tools/tests/test_models.py
from oe_ce.models import Family, Member


def test_rifle_ballistic_gets_emp_cartridge():
    fam = Family(id="cerberus", type="rifle", class_name="ballistic", experimental=False, cartridges=None, members=[])
    assert fam.resolved_cartridges() == ["standard", "ap", "hp", "emp"]


def test_pistol_must_not_include_emp():
    fam = Family(id="impaler", type="pistol", class_name="ballistic", experimental=False, cartridges=None, members=[])
    assert fam.resolved_cartridges() == ["standard", "ap", "hp"]


def test_emp_class_rifle_has_no_side_emp_cartridge():
    fam = Family(id="quasar", type="rifle", class_name="emp", experimental=False, cartridges=None, members=[])
    assert fam.resolved_cartridges() == ["standard", "ap", "hp"]
