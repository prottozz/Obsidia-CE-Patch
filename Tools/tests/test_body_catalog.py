from pathlib import Path

from oe_ce.body_load import load_body_catalog
from oe_ce.body_models import BODY_ANALOGUES


def test_load_reads_mayrequire(tmp_path):
    (tmp_path / "bodies.yaml").write_text(
        "bodies:\n"
        "  - defName: OEDominator\n"
        "    analogue: lancer\n"
        "  - defName: OEMechanicalOcto\n"
        "    analogue: scyther\n"
        "    mayRequire: Ludeon.RimWorld.Biotech\n",
        encoding="utf-8",
    )
    cat = load_body_catalog(tmp_path)
    assert cat.bodies[0].def_name == "OEDominator"
    assert cat.bodies[0].analogue == "lancer"
    assert cat.bodies[0].may_require is None
    assert cat.bodies[1].may_require == "Ludeon.RimWorld.Biotech"


def test_load_missing_file_is_empty(tmp_path):
    cat = load_body_catalog(tmp_path)
    assert cat.bodies == []


def test_analogue_keys_are_the_six():
    assert BODY_ANALOGUES == frozenset(
        {"beetle", "quadruped", "fingerspike", "scyther", "lancer", "human"}
    )
