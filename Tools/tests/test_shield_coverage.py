import os
from pathlib import Path

from oe_ce.apparel_load import load_apparel_catalog
from oe_ce.constants import (
    DEFAULT_OBSIDIA_BIOTECH,
    DEFAULT_OBSIDIA_CORE,
    DEFAULT_OBSIDIA_MU,
    DEFAULT_OBSIDIA_ROYALTY,
    DEFAULT_OBSIDIA_VEF,
)
from oe_ce.scan_shields import scan_shields
from oe_ce.shield_load import load_shield_catalog
from oe_ce.validate_shields import validate_shield_catalog

ROOT = Path(__file__).resolve().parents[2]


def _dir(env_name: str, default: str) -> Path | None:
    path = Path(os.environ.get(env_name, default))
    return path if path.is_dir() else None


def test_obsidia_shields_fully_catalogued():
    cat = load_shield_catalog(ROOT / "catalog")
    apparel = load_apparel_catalog(ROOT / "catalog")
    armor_names = {m.def_name for s in apparel.armor for m in s.members}
    scanned = scan_shields(
        Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE)),
        royalty=_dir("OBSIDIA_ROYALTY", DEFAULT_OBSIDIA_ROYALTY),
        vef=_dir("OBSIDIA_VEF", DEFAULT_OBSIDIA_VEF),
        biotech=_dir("OBSIDIA_BIOTECH", DEFAULT_OBSIDIA_BIOTECH),
        mech_upgrades=_dir("OBSIDIA_MU", DEFAULT_OBSIDIA_MU),
    )
    errs = validate_shield_catalog(cat, scanned, armor_names)
    assert errs == [], "\n".join(errs)
