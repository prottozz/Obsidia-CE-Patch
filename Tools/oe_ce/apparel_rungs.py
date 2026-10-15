from __future__ import annotations

from dataclasses import dataclass

from oe_ce.constants import RUNGS

ARMOR = "armor"
HELMET = "helmet"
APPAREL_KINDS = (ARMOR, HELMET)


@dataclass(frozen=True)
class CoverageRow:
    mult: float
    parts: tuple[str, ...]


@dataclass(frozen=True)
class ArmorStats:
    sharp: float
    blunt: float
    heat: float
    mass: float
    bulk: float
    worn_bulk: float
    carry_weight: float | None
    carry_bulk: float | None
    template: str


# Obsidia pieces never cover hands or feet, so CE's Hand rows are dropped.
COVERAGE: dict[str, tuple[CoverageRow, ...]] = {
    "armor_light": (
        CoverageRow(0.60, ("Neck",)),
        CoverageRow(0.80, ("Arm",)),
        CoverageRow(0.90, ("Leg",)),
    ),
    "armor_marine": (
        CoverageRow(0.80, ("Neck",)),
        CoverageRow(0.90, ("Arm",)),
    ),
    "armor_heavy": (CoverageRow(0.90, ("Neck",)),),
    "helmet_light": (
        CoverageRow(0.70, ("Eye",)),
        CoverageRow(0.50, ("Nose", "Jaw")),
    ),
    "helmet_marine": (CoverageRow(0.80, ("Eye", "Nose")),),
    "helmet_heavy": (CoverageRow(0.90, ("Eye",)),),
}


def _armor(
    sharp: float,
    blunt: float,
    heat: float,
    mass: float,
    carry_weight: float,
    carry_bulk: float,
    template: str,
    bulk: float = 100,
    worn_bulk: float = 15,
) -> ArmorStats:
    return ArmorStats(
        sharp, blunt, heat, mass, bulk, worn_bulk, carry_weight, carry_bulk, f"armor_{template}"
    )


def _helmet(
    sharp: float, blunt: float, heat: float, mass: float, bulk: float, template: str
) -> ArmorStats:
    return ArmorStats(sharp, blunt, heat, mass, bulk, 1, None, None, f"helmet_{template}")


ARMOR_BY_RUNG: dict[str, ArmorStats] = {
    "proto": _armor(16, 34, 0.46, 30, 50, 8, "light", bulk=80, worn_bulk=12),
    "otc": _armor(17, 38, 0.50, 40, 65, 9, "light", bulk=90, worn_bulk=13),
    "odc_t1": _armor(20, 45, 0.54, 50, 80, 10, "marine"),
    "oec": _armor(21, 47, 0.55, 52, 80, 10, "marine"),
    "oe": _armor(22, 49, 0.56, 55, 85, 12, "marine"),
    "odc_t2": _armor(24, 52, 0.58, 60, 90, 15, "heavy"),
    "odc_t3": _armor(26, 56, 0.60, 70, 95, 18, "heavy"),
    "odc_t4": _armor(28, 60, 0.62, 80, 100, 20, "heavy"),
    "omg": _armor(30, 64, 0.65, 80, 100, 20, "heavy"),
}

HELMET_BY_RUNG: dict[str, ArmorStats] = {
    "proto": _helmet(12, 26, 0.46, 3.0, 4, "light"),
    "otc": _helmet(14, 31, 0.50, 4.0, 4.5, "light"),
    "odc_t1": _helmet(16, 36, 0.54, 4.8, 5, "marine"),
    "oec": _helmet(17, 38, 0.55, 5.0, 5, "marine"),
    "oe": _helmet(18, 40, 0.56, 5.2, 5, "marine"),
    "odc_t2": _helmet(19, 43, 0.58, 5.6, 5.5, "heavy"),
    "odc_t3": _helmet(20, 46, 0.60, 6.0, 6, "heavy"),
    "odc_t4": _helmet(22, 50, 0.62, 6.6, 6, "heavy"),
    "omg": _helmet(24, 54, 0.65, 6.6, 6, "heavy"),
}

for _table in (ARMOR_BY_RUNG, HELMET_BY_RUNG):
    _table["occ"] = _table["odc_t1"]
    _table["omc"] = _table["odc_t1"]
    _table["mech"] = _table["odc_t1"]
    _table["otc_t2"] = _table["odc_t2"]
    for _alias in ("occ_reforge", "omc_mod", "oec_t2", "cac_t1", "bio_t3"):
        _table[_alias] = _table["odc_t3"]
    for _alias in ("heroic", "trophy", "cac_t2", "bio_t4"):
        _table[_alias] = _table["odc_t4"]
    assert set(_table) == set(RUNGS)


def apparel_stats(kind: str, rung: str) -> ArmorStats:
    if kind == ARMOR:
        return ARMOR_BY_RUNG[rung]
    if kind == HELMET:
        return HELMET_BY_RUNG[rung]
    raise ValueError(f"unknown apparel kind {kind}")
