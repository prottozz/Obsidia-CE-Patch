from oe_ce.emit_ammo import EMP_DEDICATED_AMOUNT, EMP_SIDE_AMOUNT, emit_ammo_xml
from oe_ce.models import Family, Member


def test_cerberus_set_and_emp_weaker_than_dedicated():
    cerb = Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")])
    quasar = Family("quasar", "rifle", "emp", members=[Member("OTC_Rifle_EMP", "otc")])
    xml = emit_ammo_xml([cerb, quasar])
    assert "AmmoSet_OE_cerberus_ballistic" in xml
    assert "Ammo_OE_cerberus_ballistic_emp" in xml
    assert "Ammo_OE_cerberus_ballistic_standard" in xml
    assert EMP_DEDICATED_AMOUNT > EMP_SIDE_AMOUNT
    assert f"<amount>{EMP_SIDE_AMOUNT}</amount>" in xml
    assert f"<amount>{EMP_DEDICATED_AMOUNT}</amount>" in xml
    assert "CE_AutoEnableCrafting_TableMachining" not in xml
    assert "<label>cerberus ballistic standard</label>" in xml
    assert "AmmoOE_cerberus_ballistic" in xml
    assert "<thingCategories>" in xml
    assert "<li>AmmoOE_cerberus_ballistic</li>" in xml
