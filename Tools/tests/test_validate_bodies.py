from oe_ce.body_models import BodyCatalog, BodyEntry
from oe_ce.scan_bodies import ScannedBody
from oe_ce.validate_bodies import validate_body_catalog

CORE = {
    "OESlimeLike": ScannedBody("OESlimeLike", [], True),
    "OEBruulLike": ScannedBody("OEBruulLike", [], True),
}


def _cat(*names_analogues):
    return BodyCatalog(
        [BodyEntry(n, a) for n, a in names_analogues]
    )


def test_good_catalog_is_clean():
    cat = _cat(("OESlimeLike", "fingerspike"), ("OEBruulLike", "beetle"))
    assert validate_body_catalog(cat, CORE) == []


def test_unknown_analogue_is_error():
    cat = _cat(("OESlimeLike", "dragon"))
    errs = validate_body_catalog(cat, CORE)
    assert any("unknown analogue" in e for e in errs)


def test_missing_core_body_is_error():
    cat = _cat(("OESlimeLike", "fingerspike"))
    errs = validate_body_catalog(cat, CORE)
    assert any("OEBruulLike" in e and "not in catalog" in e for e in errs)


def test_optional_absent_ok_when_package_missing():
    cat = BodyCatalog(
        [
            BodyEntry("OESlimeLike", "fingerspike"),
            BodyEntry("OEBruulLike", "beetle"),
            BodyEntry("OEReturnedLike", "human", may_require="Ludeon.RimWorld.Anomaly"),
        ]
    )
    assert validate_body_catalog(cat, CORE) == []


def test_optional_missing_from_present_tree_is_error():
    cat = BodyCatalog(
        [
            BodyEntry("OESlimeLike", "fingerspike"),
            BodyEntry("OEBruulLike", "beetle"),
            BodyEntry("OEReturnedLike", "human", may_require="Ludeon.RimWorld.Anomaly"),
        ]
    )
    errs = validate_body_catalog(
        cat, CORE, present_packages=frozenset({"Ludeon.RimWorld.Anomaly"})
    )
    assert any("OEReturnedLike" in e and "not an in-scope" in e for e in errs)


def test_vanilla_in_scan_is_not_coverage_error():
    scanned = dict(CORE)
    scanned["Lancer"] = ScannedBody("Lancer", [], False)
    cat = _cat(("OESlimeLike", "fingerspike"), ("OEBruulLike", "beetle"))
    assert validate_body_catalog(cat, scanned) == []
