import os
from pathlib import Path
from oe_ce.load import load_catalog
from oe_ce.scan_obsidia import scan_core_melee, scan_core_ranged
from oe_ce.validate import validate_catalog

ROOT = Path(__file__).resolve().parents[2]
CORE = Path(os.environ.get("OBSIDIA_CORE", r"C:\Projects\Assistant\294100\2519492373\1.6\Core"))


def test_core_ranged_fully_catalogued():
    cat = load_catalog(ROOT / "catalog")
    errs = validate_catalog(cat, scan_core_ranged(CORE))
    assert errs == [], "\n".join(errs)


def test_core_melee_fully_catalogued():
    cat = load_catalog(ROOT / "catalog")
    core_melee = scan_core_melee(CORE)
    catalogued = {m.def_name for m in cat.melee}
    assert len(cat.melee) == len(core_melee)
    missing = sorted(core_melee - catalogued)
    assert missing == [], f"Core melee defNames missing from catalog: {missing}"
