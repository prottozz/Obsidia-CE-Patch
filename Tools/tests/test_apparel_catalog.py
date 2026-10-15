from oe_ce.apparel_load import load_apparel_catalog
from oe_ce.apparel_models import ApparelCatalog, ApparelMember, ApparelSet
from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.scan_apparel import CoreApparel
from oe_ce.validate_apparel import validate_apparel_catalog

CORE = {
    "OCC_Armor": CoreApparel("OCC_Armor", ARMOR),
    "OCC_Armor_M": CoreApparel("OCC_Armor_M", ARMOR),
    "OCC_Armor_M_Spacer": CoreApparel("OCC_Armor_M_Spacer", ARMOR, "OCC_Armor_M"),
    "OCC_Helmet": CoreApparel("OCC_Helmet", HELMET),
}


def _armor_set(spacer_rung: str = "occ_reforge") -> ApparelSet:
    return ApparelSet(
        "occ",
        "occ",
        [
            ApparelMember("OCC_Armor"),
            ApparelMember("OCC_Armor_M", "occ_reforge"),
            ApparelMember("OCC_Armor_M_Spacer", spacer_rung),
        ],
    )


def _good() -> ApparelCatalog:
    return ApparelCatalog(
        armor=[_armor_set()],
        helmets=[ApparelSet("occ", "occ", [ApparelMember("OCC_Helmet")])],
    )


def test_good_catalog_is_clean():
    assert validate_apparel_catalog(_good(), CORE) == []


def test_member_rung_override():
    s = _armor_set()
    assert s.member_rung(s.members[0]) == "occ"
    assert s.member_rung(s.members[1]) == "occ_reforge"


def test_missing_core_piece_is_error():
    cat = ApparelCatalog(armor=[_armor_set()], helmets=[])
    errs = validate_apparel_catalog(cat, CORE)
    assert "Core apparel defName not in catalog: OCC_Helmet" in errs


def test_duplicate_is_error():
    cat = _good()
    cat.armor.append(ApparelSet("dupe", "occ", [ApparelMember("OCC_Armor")]))
    errs = validate_apparel_catalog(cat, CORE)
    assert "duplicate apparel defName OCC_Armor" in errs


def test_excluded_is_error():
    cat = _good()
    cat.armor[0].members.append(ApparelMember("OCC_Armor_M_Shield"))
    errs = validate_apparel_catalog(cat, CORE)
    assert any("OCC_Armor_M_Shield" in e and "excluded" in e for e in errs)


def test_kind_mismatch_is_error():
    cat = ApparelCatalog(
        armor=[_armor_set(), ApparelSet("occ_h", "occ", [ApparelMember("OCC_Helmet")])],
        helmets=[],
    )
    errs = validate_apparel_catalog(cat, CORE)
    assert any("OCC_Helmet" in e and "catalogued as armor" in e for e in errs)


def test_child_template_must_match_parent():
    cat = ApparelCatalog(
        armor=[_armor_set(spacer_rung="occ")],
        helmets=[ApparelSet("occ", "occ", [ApparelMember("OCC_Helmet")])],
    )
    errs = validate_apparel_catalog(cat, CORE)
    assert any("OCC_Armor_M_Spacer" in e and "coverage template" in e for e in errs)


def test_unknown_rung_is_error():
    cat = _good()
    cat.helmets[0].members[0].rung = "legendary"
    errs = validate_apparel_catalog(cat, CORE)
    assert "OCC_Helmet: unknown rung legendary" in errs


def test_load_reads_both_files(tmp_path):
    (tmp_path / "armor.yaml").write_text(
        "sets:\n"
        "  - id: occ\n"
        "    rung: occ\n"
        "    members:\n"
        "      - defName: OCC_Armor\n"
        "      - defName: OCC_Armor_M\n"
        "        rung: occ_reforge\n",
        encoding="utf-8",
    )
    (tmp_path / "helmets.yaml").write_text(
        "sets:\n"
        "  - id: occ\n"
        "    rung: occ\n"
        "    members:\n"
        "      - defName: OCC_Helmet\n",
        encoding="utf-8",
    )
    cat = load_apparel_catalog(tmp_path)
    assert [m.def_name for m in cat.armor[0].members] == ["OCC_Armor", "OCC_Armor_M"]
    assert cat.armor[0].members[1].rung == "occ_reforge"
    assert cat.armor[0].members[0].rung is None
    assert cat.helmets[0].members[0].def_name == "OCC_Helmet"
    kinds = [k for k, _s, _m in cat.entries()]
    assert kinds == [ARMOR, ARMOR, HELMET]


def test_load_missing_files_is_empty(tmp_path):
    cat = load_apparel_catalog(tmp_path)
    assert cat.armor == [] and cat.helmets == []
