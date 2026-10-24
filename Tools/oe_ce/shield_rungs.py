from __future__ import annotations

from dataclasses import dataclass

from oe_ce.apparel_rungs import ARMOR, apparel_stats
from oe_ce.constants import RUNGS

GUARDIAN = "guardian"
PROTECTOR = "protector"
ROLES = (GUARDIAN, PROTECTOR)
HANDHELD_SIZES = ("small", "medium", "big")

SIZE_MULT = {"small": 0.75, "medium": 0.90, "big": 1.10}
SIZE_CARRY = {
    "small": (5.0, 7.0, 4.0),
    "medium": (8.0, 11.0, 7.0),
    "big": (11.0, 15.0, 10.0),
}

HANDHELD_COVERAGE = {
    "small": (("Hands", "Arms", "Shoulders", "Torso"), ()),
    "medium": (("Hands", "Arms", "Shoulders", "Torso", "Neck"), ()),
    "big": (("Hands", "Arms", "Shoulders", "Torso", "Neck", "FullHead"), ("Legs",)),
}

HANDHELD_PENALTIES = {
    "small": {
        "ReloadSpeed": -0.2,
        "MeleeHitChance": -1,
        "ShootingAccuracyPawn": -0.15,
        "AimingAccuracy": -0.08,
        "Suppressability": -0.25,
        "MeleeCritChance": -0.05,
        "MeleeParryChance": 1.0,
    },
    "medium": {
        "ReloadSpeed": -0.25,
        "MeleeHitChance": -2.5,
        "ShootingAccuracyPawn": -0.28,
        "AimingAccuracy": -0.14,
        "Suppressability": -0.38,
        "MeleeCritChance": -0.12,
        "MeleeParryChance": 1.0,
    },
    "big": {
        "ReloadSpeed": -0.3,
        "MeleeHitChance": -4,
        "ShootingAccuracyPawn": -0.4,
        "AimingAccuracy": -0.2,
        "Suppressability": -0.5,
        "MeleeCritChance": -0.2,
        "MeleeParryChance": 1.0,
    },
}

INNATE_ENERGY = {
    "warqueen": (4.5, 0.75),
    "warqueen_plus": (5.25, 0.85),
    "apocriton_plus": (6.0, 1.0),
    "legionary": (2.25, 0.375),
}

_OCC_SHARP = 20.0
_OCC_MAX = 1.65
_PROTECTOR_MAX_RATIO = 0.75 / 0.90
_PROTECTOR_RECHARGE_RATIO = 0.13 / 0.11

GUARDIAN_RECHARGE = {
    "proto": 0.175,
    "otc": 0.180,
    "odc_t1": 0.195,
    "occ": 0.195,
    "omc": 0.195,
    "mech": 0.195,
    "oec": 0.200,
    "oe": 0.205,
    "odc_t2": 0.215,
    "otc_t2": 0.215,
    "odc_t3": 0.225,
    "occ_reforge": 0.225,
    "omc_mod": 0.225,
    "oec_t2": 0.225,
    "cac_t1": 0.225,
    "bio_t3": 0.225,
    "odc_t4": 0.250,
    "heroic": 0.250,
    "trophy": 0.250,
    "cac_t2": 0.250,
    "bio_t4": 0.250,
    "omg": 0.260,
}


@dataclass(frozen=True)
class EnergyStats:
    energy_max: float
    recharge: float


@dataclass(frozen=True)
class HandheldStats:
    sharp: float
    blunt: float
    heat: float
    mass: float
    bulk: float
    worn_bulk: float


def energy_stats(rung: str, role: str) -> EnergyStats:
    if rung not in GUARDIAN_RECHARGE:
        raise KeyError(rung)
    armor = apparel_stats(ARMOR, rung)
    guardian_max = round(_OCC_MAX * armor.sharp / _OCC_SHARP, 2)
    guardian_recharge = GUARDIAN_RECHARGE[rung]
    if role == GUARDIAN:
        return EnergyStats(guardian_max, guardian_recharge)
    if role == PROTECTOR:
        return EnergyStats(
            round(guardian_max * _PROTECTOR_MAX_RATIO, 2),
            round(guardian_recharge * _PROTECTOR_RECHARGE_RATIO, 3),
        )
    raise ValueError(f"unknown shield role {role}")


def handheld_stats(
    rung: str,
    size: str,
    *,
    mass: float | None = None,
    bulk: float | None = None,
    worn_bulk: float | None = None,
) -> HandheldStats:
    if size not in SIZE_MULT:
        raise ValueError(f"unknown handheld size {size}")
    armor = apparel_stats(ARMOR, rung)
    mult = SIZE_MULT[size]
    default_mass, default_bulk, default_worn = SIZE_CARRY[size]
    return HandheldStats(
        sharp=round(armor.sharp * mult, 2),
        blunt=round(armor.blunt * mult, 2),
        heat=round(armor.heat * mult, 2),
        mass=default_mass if mass is None else mass,
        bulk=default_bulk if bulk is None else bulk,
        worn_bulk=default_worn if worn_bulk is None else worn_bulk,
    )


def innate_energy(analogue: str) -> EnergyStats:
    try:
        energy_max, recharge = INNATE_ENERGY[analogue]
    except KeyError as exc:
        raise KeyError(f"unknown innate analogue {analogue}") from exc
    return EnergyStats(energy_max, recharge)


assert set(GUARDIAN_RECHARGE) == set(RUNGS)
