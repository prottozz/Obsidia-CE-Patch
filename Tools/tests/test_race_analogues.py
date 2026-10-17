import pytest

from oe_ce.race_analogues import ANALOGUES, BODY_SHAPES, race_stats


def test_spec_reference_points():
    assert race_stats("thrumbo").sharp == 14
    assert race_stats("centipede").sharp == 20
    diabolus = race_stats("diabolus")
    assert (diabolus.sharp, diabolus.blunt) == (24, 54)
    assert race_stats("warqueen_plus").sharp > race_stats("warqueen").sharp
    assert race_stats("apocriton_plus").sharp > race_stats("apocriton").sharp
    assert race_stats("warg").sharp < race_stats("megaspider").sharp < race_stats("thrumbo").sharp
    assert (
        race_stats("walker").sharp
        < race_stats("pikeman").sharp
        < race_stats("centipede").sharp
        < race_stats("diabolus").sharp
    )


def test_hide_omits_heat_walker_sets_zero():
    assert race_stats("hide").heat is None
    assert race_stats("warg").heat is None
    assert race_stats("walker").heat == 0
    assert race_stats("thrumbo").heat == 0.60


def test_body_shape_defaults():
    assert race_stats("warg").body_shape == "Quadruped"
    assert race_stats("thrumbo").body_shape == "QuadrupedTall"
    assert race_stats("warqueen").body_shape == "QuadrupedLow"
    assert race_stats("apocriton").body_shape == "Humanoid"
    assert race_stats("diabolus").body_shape in BODY_SHAPES


def test_durability_and_melee_chances():
    warg = race_stats("warg")
    assert (warg.dodge, warg.crit, warg.parry, warg.durability) == (0.23, 0.20, 0.11, 700)
    assert race_stats("warqueen").durability == 4600
    assert race_stats("warqueen_plus").durability == 5000
    assert race_stats("apocriton_plus").durability == 3400


def test_unknown_analogue_raises():
    with pytest.raises(KeyError):
        race_stats("dragon")


def test_every_row_has_allowed_body_shape():
    assert set(ANALOGUES) >= {
        "hide",
        "warg",
        "cougar",
        "megascarab",
        "megaspider",
        "thrumbo",
        "walker",
        "pikeman",
        "centipede",
        "diabolus",
        "warqueen",
        "warqueen_plus",
        "apocriton",
        "apocriton_plus",
    }
    for stats in ANALOGUES.values():
        assert stats.body_shape in BODY_SHAPES
