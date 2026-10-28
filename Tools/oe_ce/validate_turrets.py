from __future__ import annotations

from collections import Counter

from oe_ce.constants import CALIBER_BY_TYPE, DAMAGE_CLASSES, RUNGS
from oe_ce.scan_turrets import TurretScan
from oe_ce.turret_models import TurretCatalog


def validate_turret_catalog(
    cat: TurretCatalog,
    scan: TurretScan,
    *,
    present_packages: frozenset[str] = frozenset(),
) -> list[str]:
    errors: list[str] = []
    names = [g.def_name for g in cat.guns]
    for name, count in Counter(names).items():
        if count > 1:
            errors.append(f"duplicate turret gun {name}")
    # Fueled (OE_AmmoKit) turrets per gun; tacticals share a gun but carry no fuel.
    fueled: dict[str, list] = {}
    for turret in scan.turrets.values():
        if turret.fuel_capacity is not None:
            fueled.setdefault(turret.gun, []).append(turret)
    for gun in cat.guns:
        name = gun.def_name
        if gun.type not in CALIBER_BY_TYPE:
            errors.append(f"{name}: unknown type {gun.type}")
        if gun.class_name not in DAMAGE_CLASSES:
            errors.append(f"{name}: unknown class {gun.class_name}")
        if gun.rung not in RUNGS:
            errors.append(f"{name}: unknown rung {gun.rung}")
        info = scan.guns.get(name)
        if info is None:
            if gun.may_require and gun.may_require not in present_packages:
                continue
            errors.append(f"{name}: not a scanned turret gun")
            continue
        if info.package != gun.may_require:
            errors.append(f"{name}: mayRequire {gun.may_require} but defined in {info.package or 'Core'}")
        users = fueled.get(name, [])
        caps = {t.fuel_capacity for t in users}
        shots = {t.kit_shots for t in users}
        if not users:
            if gun.magazine is not None or gun.kit_shots is not None:
                errors.append(f"{name}: no OE_AmmoKit turret uses it, so no magazine / kitShots")
            continue
        if len(caps) > 1 or len(shots) > 1:
            errors.append(f"{name}: fueled turrets disagree on fuelCapacity / fuelMultiplier")
        if gun.magazine is None or float(gun.magazine) not in caps:
            errors.append(f"{name}: magazine {gun.magazine} must equal Obsidia fuelCapacity {sorted(caps)}")
        if gun.kit_shots is None or float(gun.kit_shots) not in shots:
            errors.append(f"{name}: kitShots {gun.kit_shots} must equal Obsidia fuelMultiplier {sorted(shots)}")
    for missing in sorted(set(scan.guns) - set(names)):
        errors.append(f"turret gun not in catalog: {missing}")
    for turret in sorted(scan.turrets.values(), key=lambda t: t.def_name):
        if turret.gun not in scan.guns:
            errors.append(f"{turret.def_name}: turret gun {turret.gun} not found")
    return errors
