from oe_ce.models import Member
from oe_ce.rungs import gun_stats


def test_proto_rifle_matches_charge_rifle_neighbourhood():
    s = gun_stats("rifle", Member("OE_Rifle", "proto"))
    assert s["range"] == 55
    assert s["warmup"] == 1.0
    assert s["magazine"] == 25


def test_occ_weaker_than_proto():
    proto = gun_stats("rifle", Member("OE_Rifle", "proto"))
    occ = gun_stats("rifle", Member("OCC_Rifle", "occ"))
    assert occ["range"] < proto["range"]


def test_omg_above_odc_t4():
    t4 = gun_stats("rifle", Member("X", "odc_t4"))
    omg = gun_stats("rifle", Member("Y", "omg"))
    assert omg["range"] > t4["range"]


def test_member_override_wins():
    s = gun_stats("rifle", Member("OE_Rifle", "proto", range=40.0))
    assert s["range"] == 40.0


def test_burst_clamped_to_magazine_for_bow():
    s = gun_stats("bow", Member("OES_Bow", "heroic"))
    assert s["magazine"] == 1
    assert s["burst"] == 1
