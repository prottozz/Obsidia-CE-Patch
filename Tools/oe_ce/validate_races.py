from __future__ import annotations

from collections import Counter

from oe_ce.race_analogues import ANALOGUES, BODY_SHAPES
from oe_ce.race_models import RaceCatalog
from oe_ce.scan_races import CoreRace

# TODO(slice-6): remove when validate no longer gates on boss allow-list
BIOTECH_BOSSES = frozenset(
    {
        "OE_Mech_ChaosLord",
        "OE_Mech_ArachnaQueen",
        "OE_Mech_CrimsonArachna",
        "OE_Mech_FallenLegion",
    }
)


def validate_race_catalog(cat: RaceCatalog, core: dict[str, CoreRace]) -> list[str]:
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
        if name not in core and name not in BIOTECH_BOSSES:
            errors.append(f"{name}: not an in-scope race ThingDef")
    for name, count in Counter(seen).items():
        if count > 1:
            errors.append(f"duplicate race defName {name}")
    catalogued = set(seen)
    for missing in sorted(set(core) - catalogued):
        errors.append(f"Core race defName not in catalog: {missing}")
    for boss in sorted(BIOTECH_BOSSES - catalogued):
        errors.append(f"Biotech boss defName not in catalog: {boss}")
    return errors
