from pathlib import Path

from oe_ce.apparel_load import load_apparel_catalog
from oe_ce.apparel_models import ApparelCatalog, ApparelMember, ApparelSet
from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.constants import ROYALTY_PACKAGE
from oe_ce.scan_apparel import CoreApparel
from oe_ce.validate_apparel import validate_apparel_catalog

ROOT = Path(__file__).resolve().parents[2]

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
    assert "apparel defName not in catalog: OCC_Helmet" in errs


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
        "  - id: oec\n"
        "    rung: oec\n"
        "    mayRequire: Ludeon.RimWorld.Royalty\n"
        "    members:\n"
        "      - defName: OEC_Armor\n"
        "      - defName: OEC_Armor_M\n"
        "        rung: oec_t2\n"
        "  - id: occ\n"
        "    rung: occ\n"
        "    members:\n"
        "      - defName: OCC_Armor\n"
        "      - defName: OCC_Armor_M_Jump\n"
        "        rung: occ_reforge\n"
        "        mayRequire: Ludeon.RimWorld.Royalty\n",
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
    assert cat.armor[0].id == "oec"
    assert cat.armor[0].may_require == ROYALTY_PACKAGE
    assert cat.armor[0].members[0].def_name == "OEC_Armor"
    assert cat.armor[0].members[0].may_require is None
    assert cat.armor[0].members[1].rung == "oec_t2"
    assert cat.armor[1].members[1].def_name == "OCC_Armor_M_Jump"
    assert cat.armor[1].members[1].may_require == ROYALTY_PACKAGE
    assert cat.armor[1].members[1].rung == "occ_reforge"
    assert cat.helmets[0].members[0].def_name == "OCC_Helmet"
    kinds = [k for k, _s, _m in cat.entries()]
    assert kinds == [ARMOR, ARMOR, ARMOR, ARMOR, HELMET]


def test_member_may_require_falls_back_to_set():
    s = ApparelSet(
        "oec",
        "oec",
        [ApparelMember("OEC_Armor"), ApparelMember("OEC_Armor_M", may_require="other")],
        may_require=ROYALTY_PACKAGE,
    )
    assert s.member_may_require(s.members[0]) == ROYALTY_PACKAGE
    assert s.member_may_require(s.members[1]) == "other"


def test_load_missing_files_is_empty(tmp_path):
    cat = load_apparel_catalog(tmp_path)
    assert cat.armor == [] and cat.helmets == []


def test_load_repo_catalog_includes_royalty_mayrequire():
    cat = load_apparel_catalog(ROOT / "catalog")
    armor = {m.def_name: (s, m) for s in cat.armor for m in s.members}
    helmets = {m.def_name: (s, m) for s in cat.helmets for m in s.members}
    oec = next(s for s in cat.armor if s.id == "oec")
    assert oec.may_require == ROYALTY_PACKAGE
    assert "OEC_Armor" in armor
    assert "OEC_Armor_M" in armor
    assert "OCC_Armor_M_Jump" in armor
    assert armor["OCC_Armor_M_Jump"][1].may_require == ROYALTY_PACKAGE
    assert armor["OCC_Armor_M_Jump"][1].rung == "occ_reforge"
    assert "OEC_Helmet" in helmets
    assert "ODC_Helmet_Prestige" in helmets
    assert "OMG_Trophy_Helmet_Neuroflash" in helmets
    assert "OEC_Armor_M_Grenadier" not in armor
    assert "OEC_Armor_M_Shield" not in armor
    assert "OEC_Armor_M_Barrier" not in armor


def test_load_reads_member_mass_overrides(tmp_path):
    (tmp_path / "armor.yaml").write_text(
        "sets:\n"
        "  - id: kid\n"
        "    rung: proto\n"
        "    mayRequire: Ludeon.RimWorld.Biotech\n"
        "    members:\n"
        "      - defName: OE_Armor_Kid\n"
        "        mass: 18\n"
        "        bulk: 50\n"
        "        wornBulk: 7\n",
        encoding="utf-8",
    )
    member = load_apparel_catalog(tmp_path).armor[0].members[0]
    assert (member.mass, member.bulk, member.worn_bulk) == (18, 50, 7)


def _dlc_cat(may_require: str | None) -> ApparelCatalog:
    return ApparelCatalog(
        armor=[
            _armor_set(),
            ApparelSet(
                "occ_dlc",
                "occ_reforge",
                [ApparelMember("OCC_Armor_M_Turret", may_require=may_require)],
            ),
        ],
        helmets=[ApparelSet("occ", "occ", [ApparelMember("OCC_Helmet")])],
    )


def test_missing_dlc_row_skipped_when_tree_absent():
    from oe_ce.constants import ANOMALY_PACKAGE

    assert validate_apparel_catalog(_dlc_cat(ANOMALY_PACKAGE), CORE) == []
    errs = validate_apparel_catalog(
        _dlc_cat(ANOMALY_PACKAGE), CORE, present_packages=frozenset({ANOMALY_PACKAGE})
    )
    assert "OCC_Armor_M_Turret: not an in-scope apparel def" in errs


def test_may_require_must_match_scanned_package():
    from oe_ce.constants import ANOMALY_PACKAGE, BIOTECH_PACKAGE

    scanned = dict(CORE)
    scanned["OCC_Armor_M_Turret"] = CoreApparel(
        "OCC_Armor_M_Turret", ARMOR, "OCC_Armor_M", ANOMALY_PACKAGE
    )
    ok = validate_apparel_catalog(_dlc_cat(ANOMALY_PACKAGE), scanned)
    assert ok == []
    for wrong in (None, BIOTECH_PACKAGE):
        errs = validate_apparel_catalog(_dlc_cat(wrong), scanned)
        assert any("OCC_Armor_M_Turret: mayRequire" in e for e in errs), wrong
