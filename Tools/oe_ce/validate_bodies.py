from __future__ import annotations

from collections import Counter

from oe_ce.body_models import BODY_ANALOGUES, BodyCatalog
from oe_ce.scan_bodies import ScannedBody


def validate_body_catalog(
    cat: BodyCatalog,
    scanned: dict[str, ScannedBody],
    *,
    present_packages: frozenset[str] = frozenset(),
) -> list[str]:
    errors: list[str] = []
    seen: list[str] = []
    for entry in cat.bodies:
        name = entry.def_name
        seen.append(name)
        if entry.analogue not in BODY_ANALOGUES:
            errors.append(f"{name}: unknown analogue {entry.analogue}")
        info = scanned.get(name)
        if info is None or not info.custom:
            pkg = entry.may_require
            if pkg and pkg not in present_packages:
                continue
            errors.append(f"{name}: not an in-scope BodyDef")
    for name, count in Counter(seen).items():
        if count > 1:
            errors.append(f"duplicate BodyDef {name}")
    catalogued = set(seen)
    for name, info in scanned.items():
        if info.custom and name not in catalogued:
            errors.append(f"BodyDef not in catalog: {name}")
    return errors
