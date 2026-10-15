import pytest

from oe_ce.apparel_rungs import (
    ARMOR,
    ARMOR_BY_RUNG,
    COVERAGE,
    HELMET,
    HELMET_BY_RUNG,
    apparel_stats,
)
from oe_ce.constants import RUNGS


def test_every_rung_has_armor_and_helmet_rows():
    assert set(ARMOR_BY_RUNG) == set(RUNGS)
    assert set(HELMET_BY_RUNG) == set(RUNGS)


def test_occ_is_ce_marine():
    occ = apparel_stats(ARMOR, "occ")
    assert (occ.sharp, occ.blunt, occ.heat) == (20, 45, 0.54)
    assert occ.template == "armor_marine"
    helm = apparel_stats(HELMET, "occ")
    assert (helm.sharp, helm.blunt) == (16, 36)
    assert helm.template == "helmet_marine"


def test_otc_strictly_below_occ_at_both_tiers():
    for kind in (ARMOR, HELMET):
        otc = apparel_stats(kind, "otc")
        occ = apparel_stats(kind, "occ")
        assert otc.sharp < occ.sharp and otc.blunt < occ.blunt
        otc_t2 = apparel_stats(kind, "otc_t2")
        occ_reforge = apparel_stats(kind, "occ_reforge")
        assert otc_t2.sharp < occ_reforge.sharp and otc_t2.blunt < occ_reforge.blunt


def test_armor_ladder_order():
    ladder = ["proto", "otc", "occ", "oec", "oe", "odc_t2", "odc_t3", "odc_t4", "omg"]
    sharps = [apparel_stats(ARMOR, r).sharp for r in ladder]
    assert sharps == sorted(sharps)
    assert len(set(sharps)) == len(sharps)
    assert apparel_stats(ARMOR, "omc").sharp == apparel_stats(ARMOR, "occ").sharp
    assert apparel_stats(ARMOR, "odc_t4").sharp == 28
    assert apparel_stats(ARMOR, "heroic") == apparel_stats(ARMOR, "odc_t4")
    assert apparel_stats(ARMOR, "bio_t3") == apparel_stats(ARMOR, "odc_t3")
    assert apparel_stats(ARMOR, "mech") == apparel_stats(ARMOR, "omc")


def test_body_armor_carries_helmets_do_not():
    for rung in RUNGS:
        assert apparel_stats(ARMOR, rung).carry_weight is not None
        assert apparel_stats(HELMET, rung).carry_weight is None
    assert apparel_stats(ARMOR, "occ").carry_weight == 80
    assert apparel_stats(ARMOR, "odc_t4").carry_bulk == 20


def test_templates_exist_and_match_kind():
    for rung in RUNGS:
        assert apparel_stats(ARMOR, rung).template.startswith("armor_")
        assert apparel_stats(HELMET, rung).template.startswith("helmet_")
        assert apparel_stats(ARMOR, rung).template in COVERAGE
        assert apparel_stats(HELMET, rung).template in COVERAGE
    arm_parts = {p for row in COVERAGE["armor_light"] for p in row.parts}
    assert arm_parts == {"Neck", "Arm", "Leg"}
    helm_parts = {p for row in COVERAGE["helmet_marine"] for p in row.parts}
    assert "Arm" not in helm_parts and "Eye" in helm_parts


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        apparel_stats("cloak", "occ")
