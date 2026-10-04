import os
from pathlib import Path
from oe_ce.load import load_catalog
from oe_ce.scan_obsidia import scan_core_ranged
from oe_ce.validate import validate_catalog

ROOT = Path(__file__).resolve().parents[2]
CORE = Path(os.environ.get("OBSIDIA_CORE", r"C:\Projects\Assistant\294100\2519492373\1.6\Core"))


def test_core_ranged_fully_catalogued():
    cat = load_catalog(ROOT / "catalog")
    errs = validate_catalog(cat, scan_core_ranged(CORE))
    assert errs == [], "\n".join(errs)
