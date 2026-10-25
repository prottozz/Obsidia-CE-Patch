from pathlib import Path

from oe_ce.constants import ANOMALY_PACKAGE, BIOTECH_PACKAGE, IDEOLOGY_PACKAGE
from oe_ce.race_analogues import ANIMAL, MECHANOID
from oe_ce.race_load import load_race_catalog
from oe_ce.race_models import RaceCatalog, RaceMember, RaceSet
from oe_ce.scan_races import CoreRace
from oe_ce.validate_races import validate_race_catalog

CORE = {
    "OE_Direwolf": CoreRace("OE_Direwolf", ANIMAL),
    "OE_Elder_Direwolf": CoreRace("OE_Elder_Direwolf", ANIMAL),
    "OE_Mech_DarkCrusader": CoreRace("OE_Mech_DarkCrusader", MECHANOID),
}


def _good() -> RaceCatalog:
    return RaceCatalog(
        sets=[
            RaceSet(
                "direwolf",
                "warg",
                members=[
                    RaceMember("OE_Direwolf"),
                    RaceMember("OE_Elder_Direwolf", analogue="thrumbo"),
                ],
            ),
            RaceSet("crusader", "centipede", "Humanoid", [RaceMember("OE_Mech_DarkCrusader")]),
            RaceSet(
                "chaos_lord",
                "diabolus",
                "Humanoid",
                [RaceMember("OE_Mech_ChaosLord")],
                may_require="Ludeon.RimWorld.Biotech",
            ),
            RaceSet(
                "arachna_queen",
                "warqueen",
                members=[RaceMember("OE_Mech_ArachnaQueen")],
                may_require="Ludeon.RimWorld.Biotech",
            ),
            RaceSet(
                "crimson_arachna",
                "warqueen_plus",
                members=[RaceMember("OE_Mech_CrimsonArachna")],
                may_require="Ludeon.RimWorld.Biotech",
            ),
            RaceSet(
                "fallen_legion",
                "apocriton_plus",
                members=[RaceMember("OE_Mech_FallenLegion")],
                may_require="Ludeon.RimWorld.Biotech",
            ),
        ]
    )


def test_good_catalog_is_clean():
    assert validate_race_catalog(_good(), CORE) == []


def test_member_analogue_and_body_shape_override():
    s = _good().sets[0]
    assert s.member_analogue(s.members[0]) == "warg"
    assert s.member_analogue(s.members[1]) == "thrumbo"
    assert s.member_body_shape(s.members[0]) == "Quadruped"
    assert s.member_body_shape(s.members[1]) == "QuadrupedTall"
    crusader = _good().sets[1]
    assert crusader.member_body_shape(crusader.members[0]) == "Humanoid"


def test_missing_core_race_is_error():
    cat = _good()
    cat.sets[0].members.pop()
    errs = validate_race_catalog(cat, CORE)
    assert "Core race defName not in catalog: OE_Elder_Direwolf" in errs


def test_duplicate_is_error():
    cat = _good()
    cat.sets.append(RaceSet("dupe", "warg", members=[RaceMember("OE_Direwolf")]))
    errs = validate_race_catalog(cat, CORE)
    assert "duplicate race defName OE_Direwolf" in errs


def test_unknown_analogue_is_error():
    cat = _good()
    cat.sets[0].members[0].analogue = "dragon"
    errs = validate_race_catalog(cat, CORE)
    assert "OE_Direwolf: unknown analogue dragon" in errs


def test_unknown_body_shape_is_error():
    cat = _good()
    cat.sets[0].members[0].body_shape = "Blob"
    errs = validate_race_catalog(cat, CORE)
    assert "OE_Direwolf: unknown bodyShape Blob" in errs


def test_excluded_bullet_catalogued_is_error():
    cat = _good()
    cat.sets[0].members.append(RaceMember("Bullet_Bruul_Acid"))
    errs = validate_race_catalog(cat, CORE)
    assert any("Bullet_Bruul_Acid" in e and "not an in-scope" in e for e in errs)


def test_optional_member_absent_from_scan_is_ok_when_package_missing():
    cat = RaceCatalog(sets=[
        RaceSet("direwolf", "warg", members=[RaceMember("OE_Direwolf"), RaceMember("OE_Elder_Direwolf")]),
        RaceSet("crusader", "centipede", "Humanoid", [RaceMember("OE_Mech_DarkCrusader")]),
        RaceSet(
            "maid",
            "walker",
            "Humanoid",
            [RaceMember("OE_Mech_Maid")],
            may_require="Ludeon.RimWorld.Biotech",
        ),
    ])
    assert validate_race_catalog(cat, CORE) == []


def test_optional_member_missing_from_present_tree_is_error():
    cat = RaceCatalog(sets=[
        RaceSet("direwolf", "warg", members=[RaceMember("OE_Direwolf"), RaceMember("OE_Elder_Direwolf")]),
        RaceSet("crusader", "centipede", "Humanoid", [RaceMember("OE_Mech_DarkCrusader")]),
        RaceSet(
            "maid",
            "walker",
            "Humanoid",
            [RaceMember("OE_Mech_Maid")],
            may_require="Ludeon.RimWorld.Biotech",
        ),
    ])
    errs = validate_race_catalog(
        cat, CORE, present_packages=frozenset({"Ludeon.RimWorld.Biotech"})
    )
    assert any("OE_Mech_Maid" in e and "not an in-scope" in e for e in errs)


def test_scanned_dlc_race_must_be_catalogued():
    scanned = dict(CORE)
    scanned["OE_Mech_Maid"] = CoreRace("OE_Mech_Maid", MECHANOID)
    cat = _good()  # no Maid
    errs = validate_race_catalog(
        cat, scanned, present_packages=frozenset({"Ludeon.RimWorld.Biotech"})
    )
    assert any("OE_Mech_Maid" in e and "not in catalog" in e for e in errs)


def test_load_reads_overrides(tmp_path):
    (tmp_path / "races.yaml").write_text(
        "sets:\n"
        "  - id: direwolf\n"
        "    analogue: warg\n"
        "    members:\n"
        "      - defName: OE_Direwolf\n"
        "      - defName: OE_Elder_Direwolf\n"
        "        analogue: thrumbo\n"
        "  - id: chaos_lord\n"
        "    analogue: diabolus\n"
        "    bodyShape: Humanoid\n"
        "    mayRequire: Ludeon.RimWorld.Biotech\n"
        "    members:\n"
        "      - defName: OE_Mech_ChaosLord\n"
        "  - id: arachna\n"
        "    analogue: megaspider\n"
        "    members:\n"
        "      - defName: OE_Arachna_Blue\n"
        "      - defName: OE_Arachna_Tox\n"
        "        mayRequire: Ludeon.RimWorld.Biotech\n",
        encoding="utf-8",
    )
    cat = load_race_catalog(tmp_path)
    assert cat.sets[0].member_analogue(cat.sets[0].members[1]) == "thrumbo"
    assert cat.sets[1].body_shape == "Humanoid"
    assert cat.sets[1].members[0].def_name == "OE_Mech_ChaosLord"
    assert cat.sets[1].may_require == "Ludeon.RimWorld.Biotech"
    assert cat.sets[2].members[1].may_require == "Ludeon.RimWorld.Biotech"


def test_member_may_require_falls_back_to_set():
    s = RaceSet(
        "chaos_slime",
        "hide",
        "QuadrupedLow",
        [RaceMember("OE_ChaosSlime_Larval"), RaceMember("OE_ChaosSlime_Goliath", may_require="x")],
        may_require="Ludeon.RimWorld.Anomaly",
    )
    assert s.member_may_require(s.members[0]) == "Ludeon.RimWorld.Anomaly"
    assert s.member_may_require(s.members[1]) == "x"


def test_load_missing_file_is_empty(tmp_path):
    cat = load_race_catalog(tmp_path)
    assert cat.sets == []


ROOT = Path(__file__).resolve().parents[2]


def test_load_repo_catalog_dlc_mayrequire():
    cat = load_race_catalog(ROOT / "catalog")
    by_name = {
        m.def_name: cat.sets[i].member_may_require(m)
        for i, s in enumerate(cat.sets)
        for m in s.members
    }
    assert by_name["OE_Arachna_Tox"] == BIOTECH_PACKAGE
    assert by_name["OE_Mech_Maid"] == BIOTECH_PACKAGE
    assert by_name["OE_ChaosSlime_Invincible"] == ANOMALY_PACKAGE
    assert by_name["OE_Dryad_Synthesis"] == IDEOLOGY_PACKAGE
    assert by_name["OE_Mech_ChaosLord"] == BIOTECH_PACKAGE
    inv = next(m for s in cat.sets for m in s.members if m.def_name == "OE_ChaosSlime_Invincible")
    s = next(s for s in cat.sets for m in s.members if m.def_name == inv.def_name)
    assert s.member_analogue(inv) == "thrumbo"
    assert s.member_body_shape(inv) == "QuadrupedTall"
