from __future__ import annotations

from collections import Counter

from oe_ce.race_analogues import ANALOGUES, BODY_SHAPES
from oe_ce.race_models import RaceCatalog
from oe_ce.scan_races import CoreRace


def validate_race_catalog(
    cat: RaceCatalog,
    scanned: dict[str, CoreRace],
    *,
    present_packages: frozenset[str] = frozenset(),
) -> list[str]:
    errors: list[str] = []
    seen: list[str] = []
    for race_set, member in cat.entries():
        name = member.def_name
        analogue = race_set.member_analogue(member)
        seen.append(name)
        if analogue not in ANALOGUES:
            errors.append(f"{name}: unknown analogue {analogue}")
            shape = member.body_shape or race_set.body_shape
        else:
            shape = race_set.member_body_shape(member)
        if shape is not None and shape not in BODY_SHAPES:
            errors.append(f"{name}: unknown bodyShape {shape}")
        if name not in scanned:
            pkg = race_set.member_may_require(member)
            if pkg and pkg not in present_packages:
                continue
            errors.append(f"{name}: not an in-scope race ThingDef")
    for name, count in Counter(seen).items():
        if count > 1:
            errors.append(f"duplicate race defName {name}")
    catalogued = set(seen)
    for missing in sorted(set(scanned) - catalogued):
        errors.append(f"Core race defName not in catalog: {missing}")
    return errors
