from __future__ import annotations

from oe_ce.constants import RUNGS
from oe_ce.models import Member

TYPE_RANGE_MULT = {
    "pistol": 0.55,
    "smg": 0.65,
    "shotgun": 0.40,
    "rifle": 1.0,
    "sniper": 1.25,
    "bow": 0.90,
    "lmg": 0.95,
    "minigun": 0.70,
    "launcher": 0.80,
    "rocket": 1.10,
}

TYPE_MAG = {
    "pistol": 12,
    "smg": 25,
    "shotgun": 8,
    "rifle": 25,
    "sniper": 8,
    "bow": 1,
    "lmg": 50,
    "minigun": 80,
    "launcher": 6,
    "rocket": 1,
}


def _rifle_row(range_val: float) -> dict:
    return {
        "range": range_val,
        "warmup": 1.0,
        "magazine": 25,
        "reload": 4.0,
        "spread": 0.08,
        "sway": 1.20,
        "recoil": 1.46,
        "cooldown": 0.36,
        "burst": 6,
        "mass": 3.0,
        "bulk": 7.0,
    }


RIFLE_BY_RUNG: dict[str, dict] = {
    "proto": _rifle_row(55),
    "odc_t1": _rifle_row(48),
    "odc_t2": _rifle_row(62),
    "odc_t3": _rifle_row(68),
    "odc_t4": _rifle_row(75),
    "otc": _rifle_row(50),
    "omc": _rifle_row(52),
    "oec": _rifle_row(53),
    "oe": _rifle_row(54),
    "omg": _rifle_row(78),
}

RIFLE_BY_RUNG["occ"] = dict(RIFLE_BY_RUNG["odc_t1"])

for _alias in (
    "occ_reforge",
    "omc_mod",
    "oec_t2",
    "otc_t2",
    "cac_t1",
    "bio_t3",
):
    RIFLE_BY_RUNG[_alias] = dict(RIFLE_BY_RUNG["odc_t3"])

for _alias in ("cac_t2", "bio_t4", "heroic", "trophy"):
    RIFLE_BY_RUNG[_alias] = dict(RIFLE_BY_RUNG["odc_t4"])

RIFLE_BY_RUNG["mech"] = dict(RIFLE_BY_RUNG["omc"])

assert set(RIFLE_BY_RUNG) == set(RUNGS)


def gun_stats(weapon_type: str, member: Member) -> dict:
    row = dict(RIFLE_BY_RUNG[member.rung])
    row["range"] = round(row["range"] * TYPE_RANGE_MULT[weapon_type], 2)
    row["magazine"] = TYPE_MAG[weapon_type]
    if member.rung == "mech":
        row["magazine"] = max(row["magazine"], 40)
    if weapon_type == "bow":
        row["reload"] = 3.5
    mapping = {
        "range": member.range,
        "warmup": member.warmup,
        "burst": member.burst,
        "magazine": member.magazine,
        "spread": member.spread,
        "mass": member.mass,
        "bulk": member.bulk,
    }
    for key, val in mapping.items():
        if val is not None:
            row[key] = val
    burst = row.get("burst")
    if burst is not None and burst > row["magazine"]:
        row["burst"] = row["magazine"]
    return row
