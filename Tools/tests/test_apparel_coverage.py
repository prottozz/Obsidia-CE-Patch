import os
from pathlib import Path

from oe_ce.apparel_load import load_apparel_catalog
from oe_ce.apparel_rungs import ARMOR, HELMET, apparel_stats
from oe_ce.constants import (
    ANOMALY_PACKAGE,
    BIOTECH_PACKAGE,
    DEFAULT_OBSIDIA_ANOMALY,
    DEFAULT_OBSIDIA_BIOTECH,
    DEFAULT_OBSIDIA_CORE,
    DEFAULT_OBSIDIA_ODYSSEY,
    DEFAULT_OBSIDIA_ROYALTY,
    ODYSSEY_PACKAGE,
    ROYALTY_PACKAGE,
)
from oe_ce.scan_apparel import scan_core_apparel
from oe_ce.validate_apparel import validate_apparel_catalog

ROOT = Path(__file__).resolve().parents[2]
CORE = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))
ROYALTY = Path(os.environ.get("OBSIDIA_ROYALTY", DEFAULT_OBSIDIA_ROYALTY))


def _dir(env_name: str, default: str) -> Path | None:
    path = Path(os.environ.get(env_name, default))
    return path if path.is_dir() else None


def _trees() -> dict[str, Path | None]:
    return {
        ROYALTY_PACKAGE: _dir("OBSIDIA_ROYALTY", DEFAULT_OBSIDIA_ROYALTY),
        BIOTECH_PACKAGE: _dir("OBSIDIA_BIOTECH", DEFAULT_OBSIDIA_BIOTECH),
        ANOMALY_PACKAGE: _dir("OBSIDIA_ANOMALY", DEFAULT_OBSIDIA_ANOMALY),
        ODYSSEY_PACKAGE: _dir("OBSIDIA_ODYSSEY", DEFAULT_OBSIDIA_ODYSSEY),
    }


def _rung(sets, def_name):
    for s in sets:
        for m in s.members:
            if m.def_name == def_name:
                return s.member_rung(m)
    raise KeyError(def_name)


def test_core_and_dlc_apparel_fully_catalogued():
    cat = load_apparel_catalog(ROOT / "catalog")
    trees = _trees()
    scanned = scan_core_apparel(
        CORE,
        trees[ROYALTY_PACKAGE],
        biotech=trees[BIOTECH_PACKAGE],
        anomaly=trees[ANOMALY_PACKAGE],
        odyssey=trees[ODYSSEY_PACKAGE],
    )
    present = frozenset(pkg for pkg, path in trees.items() if path is not None)
    errs = validate_apparel_catalog(cat, scanned, present_packages=present)
    assert errs == [], "\n".join(errs)


def test_dlc_variants_share_their_kit_plate():
    cat = load_apparel_catalog(ROOT / "catalog")
    rungs = {m.def_name: s.member_rung(m) for s in cat.armor for m in s.members}
    for variant, base in (
        ("OCC_Armor_M_Mechanitor", "OCC_Armor_M"),
        ("OCC_Armor_M_Turret", "OCC_Armor_M"),
        ("OTC_Armor_M_Turret", "OTC_Armor_M"),
        ("ODC_Armor_Duelist_Turret", "ODC_Armor_Duelist"),
        ("CAC_HeavyArmor_Swarmling", "CAC_HeavyArmor"),
        ("OMG_Armor_Commando", "OMG_Armor_Corsair"),
        ("EGO_Armor_Shell_Mechanitor", "EGO_Armor_Shell_Ranged"),
    ):
        assert rungs[variant] == rungs[base], variant


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
