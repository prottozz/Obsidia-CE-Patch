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
            RaceSet("chaos_lord", "diabolus", "Humanoid", [RaceMember("OE_Mech_ChaosLord")]),
            RaceSet("arachna_queen", "warqueen", members=[RaceMember("OE_Mech_ArachnaQueen")]),
            RaceSet(
                "crimson_arachna",
                "warqueen_plus",
                members=[RaceMember("OE_Mech_CrimsonArachna")],
            ),
            RaceSet(
                "fallen_legion",
                "apocriton_plus",
                members=[RaceMember("OE_Mech_FallenLegion")],
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


def test_missing_biotech_boss_is_error_even_without_scan():
    cat = _good()
    cat.sets = [s for s in cat.sets if s.id != "chaos_lord"]
    errs = validate_race_catalog(cat, CORE)
    assert "Biotech boss defName not in catalog: OE_Mech_ChaosLord" in errs


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
        "    members:\n"
        "      - defName: OE_Mech_ChaosLord\n",
        encoding="utf-8",
    )
    cat = load_race_catalog(tmp_path)
    assert cat.sets[0].member_analogue(cat.sets[0].members[1]) == "thrumbo"
    assert cat.sets[1].body_shape == "Humanoid"
    assert cat.sets[1].members[0].def_name == "OE_Mech_ChaosLord"


def test_load_missing_file_is_empty(tmp_path):
    cat = load_race_catalog(tmp_path)
    assert cat.sets == []
