import os
from pathlib import Path

from oe_ce.constants import DEFAULT_OBSIDIA_BIOTECH, DEFAULT_OBSIDIA_CORE
from oe_ce.race_analogues import ANALOGUES, race_stats
from oe_ce.race_load import load_race_catalog
from oe_ce.scan_races import scan_races
from oe_ce.validate_races import validate_race_catalog

ROOT = Path(__file__).resolve().parents[2]
CORE = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))
BIOTECH = Path(os.environ.get("OBSIDIA_BIOTECH", DEFAULT_OBSIDIA_BIOTECH))


def test_core_races_fully_catalogued():
    cat = load_race_catalog(ROOT / "catalog")
    bio = BIOTECH if (BIOTECH / "Defs" / "ThingDefs_Races").is_dir() else None
    errs = validate_race_catalog(cat, scan_races(CORE, bio))
    assert errs == [], "\n".join(errs)


def test_catalog_analogues_exist_and_elders_outscale_adults():
    cat = load_race_catalog(ROOT / "catalog")
    used = {s.member_analogue(m) for s in cat.sets for m in s.members}
    assert used <= set(ANALOGUES)
    by_name = {m.def_name: s.member_analogue(m) for s in cat.sets for m in s.members}
    assert race_stats(by_name["OE_Direwolf"]).sharp < race_stats(by_name["OE_Elder_Direwolf"]).sharp
    assert by_name["OE_Mech_ChaosLord"] == "diabolus"
    assert by_name["OE_Mech_ArachnaQueen"] == "warqueen"
    assert by_name["OE_Mech_CrimsonArachna"] == "warqueen_plus"
    assert by_name["OE_Mech_FallenLegion"] == "apocriton_plus"
    assert by_name["OE_Mech_CAC_Arachna"] == "pikeman"
