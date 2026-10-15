import os
from pathlib import Path

from oe_ce.apparel_load import load_apparel_catalog
from oe_ce.apparel_rungs import ARMOR, HELMET, apparel_stats
from oe_ce.constants import DEFAULT_OBSIDIA_CORE
from oe_ce.scan_apparel import scan_core_apparel
from oe_ce.validate_apparel import validate_apparel_catalog

ROOT = Path(__file__).resolve().parents[2]
CORE = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))


def _rung(sets, def_name):
    for s in sets:
        for m in s.members:
            if m.def_name == def_name:
                return s.member_rung(m)
    raise KeyError(def_name)


def test_core_apparel_fully_catalogued():
    cat = load_apparel_catalog(ROOT / "catalog")
    errs = validate_apparel_catalog(cat, scan_core_apparel(CORE))
    assert errs == [], "\n".join(errs)


def test_catalog_keeps_otc_below_occ():
    cat = load_apparel_catalog(ROOT / "catalog")
    pairs = [
        (ARMOR, cat.armor, "OTC_Armor", "OCC_Armor"),
        (ARMOR, cat.armor, "OTC_Armor_M", "OCC_Armor_M"),
        (HELMET, cat.helmets, "OTC_Helmet", "OCC_Helmet"),
        (HELMET, cat.helmets, "OTC_Helmet_M", "OCC_Helmet_M"),
    ]
    for kind, sets, otc, occ in pairs:
        weak = apparel_stats(kind, _rung(sets, otc))
        strong = apparel_stats(kind, _rung(sets, occ))
        assert weak.sharp < strong.sharp, (otc, occ)
        assert weak.blunt < strong.blunt, (otc, occ)
