from oe_ce.emit_ammo import EMP_DEDICATED_AMOUNT, EMP_SIDE_AMOUNT, emit_ammo_xml
from oe_ce.models import Family, Member
from oe_ce.validate import validate_emp_constants


def test_emp_constants():
    assert validate_emp_constants() == []
    assert EMP_DEDICATED_AMOUNT > EMP_SIDE_AMOUNT


def test_ammo_trade_tags():
    xml = emit_ammo_xml([Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")])])
    assert "CE_AutoEnableTrade" in xml
    assert "OEGear" in xml
    assert "CE_AutoEnableCrafting_TableMachining" not in xml
