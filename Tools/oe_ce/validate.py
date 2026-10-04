from __future__ import annotations

from collections import Counter

from oe_ce.constants import DAMAGE_CLASSES, ELEMENTAL_CLASSES, EMP_SIDE_TYPES, RUNGS, WEAPON_TYPES
from oe_ce.emit_ammo import EMP_DEDICATED_AMOUNT, EMP_SIDE_AMOUNT
from oe_ce.models import Catalog


def validate_emp_constants() -> list[str]:
    if EMP_DEDICATED_AMOUNT > EMP_SIDE_AMOUNT:
        return []
    return [
        "EMP_DEDICATED_AMOUNT must be greater than EMP_SIDE_AMOUNT "
        f"({EMP_DEDICATED_AMOUNT} <= {EMP_SIDE_AMOUNT})"
    ]


def validate_catalog(catalog: Catalog, core_ranged: set[str]) -> list[str]:
    errors: list[str] = list(validate_emp_constants())
    seen: list[str] = []
    for fam in catalog.families:
        if fam.type not in WEAPON_TYPES:
            errors.append(f"{fam.id}: unknown type {fam.type}")
        if fam.class_name not in DAMAGE_CLASSES:
            errors.append(f"{fam.id}: unknown class {fam.class_name}")
        carts = fam.resolved_cartridges()
        if fam.class_name in ELEMENTAL_CLASSES and carts != [fam.class_name]:
            errors.append(
                f"{fam.id}: {fam.class_name} must have a single {fam.class_name} cartridge"
            )
        if (
            fam.type in ("pistol", "smg")
            and fam.class_name != "emp"
            and "emp" in carts
        ):
            errors.append(f"{fam.id}: pistol/smg must not have emp cartridge")
        if (
            fam.class_name == "ballistic"
            and fam.type in EMP_SIDE_TYPES
            and "emp" not in carts
        ):
            errors.append(f"{fam.id}: {fam.type} {fam.class_name} missing emp cartridge")
        for m in fam.members:
            seen.append(m.def_name)
            if m.rung not in RUNGS:
                errors.append(f"{m.def_name}: unknown rung {m.rung}")
    counts = Counter(seen)
    for name, n in counts.items():
        if n > 1:
            errors.append(f"duplicate defName {name}")
    catalogued = set(seen)
    for missing in sorted(core_ranged - catalogued):
        errors.append(f"Core ranged defName not in catalog: {missing}")
    return errors
