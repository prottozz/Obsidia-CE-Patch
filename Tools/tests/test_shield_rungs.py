from oe_ce.constants import RUNGS
from oe_ce.shield_rungs import (
    GUARDIAN,
    PROTECTOR,
    energy_stats,
    handheld_stats,
    innate_energy,
)


def test_every_rung_has_guardian_and_protector_energy():
    for rung in RUNGS:
        g = energy_stats(rung, GUARDIAN)
        p = energy_stats(rung, PROTECTOR)
        assert g.energy_max > 0 and g.recharge > 0
        assert p.energy_max < g.energy_max
        assert p.recharge > g.recharge


def test_occ_guardian_matches_ce_shield_belt():
    g = energy_stats("occ", GUARDIAN)
    assert (g.energy_max, g.recharge) == (1.65, 0.195)


def test_otc_guardian_below_occ_heroic_above():
    otc = energy_stats("otc", GUARDIAN)
    occ = energy_stats("occ", GUARDIAN)
    heroic = energy_stats("heroic", GUARDIAN)
    assert otc.energy_max < occ.energy_max
    assert heroic.energy_max > occ.energy_max


def test_occ_reforge_aliases_share_energy():
    base = energy_stats("occ_reforge", GUARDIAN)
    for rung in ("odc_t3", "omc_mod", "oec_t2", "cac_t1", "bio_t3"):
        assert energy_stats(rung, GUARDIAN) == base


def test_odc_t2_small_handheld_matches_spec_row():
    s = handheld_stats("odc_t2", "small")
    assert (s.sharp, s.blunt, s.heat) == (18, 39, 0.43)
    assert (s.mass, s.bulk, s.worn_bulk) == (5, 7, 4)


def test_handheld_mass_override():
    s = handheld_stats("heroic", "small", mass=4)
    assert s.mass == 4
    assert s.sharp == 21


def test_oes_big_and_omg_medium_overrides():
    oes = handheld_stats("heroic", "big", mass=10)
    assert (oes.sharp, oes.blunt, oes.heat) == (30.8, 66, 0.68)
    assert oes.mass == 10
    omg = handheld_stats("omg", "medium", bulk=12, worn_bulk=8)
    assert (omg.sharp, omg.blunt, omg.heat) == (27, 57.6, 0.59)
    assert (omg.mass, omg.bulk, omg.worn_bulk) == (8, 12, 8)


def test_innate_warqueen_matches_ce():
    s = innate_energy("warqueen")
    assert (s.energy_max, s.recharge) == (4.5, 0.75)
    plus = innate_energy("warqueen_plus")
    assert plus.energy_max > s.energy_max
    fallen = innate_energy("apocriton_plus")
    assert (fallen.energy_max, fallen.recharge) == (6.0, 1.0)
    dom = innate_energy("legionary")
    assert (dom.energy_max, dom.recharge) == (2.25, 0.375)
