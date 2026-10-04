from __future__ import annotations

import os
import sys
from pathlib import Path

from oe_ce.emit_ammo import emit_ammo_xml
from oe_ce.emit_guns import emit_gun_patches
from oe_ce.emit_melee import emit_melee_xml
from oe_ce.emit_pawnkinds import emit_pawnkind_xml
from oe_ce.emit_recipes import emit_recipe_xml
from oe_ce.load import load_catalog
from oe_ce.scan_obsidia import scan_core_ranged
from oe_ce.validate import validate_catalog

_DEFAULT_CORE = Path(r"C:\Projects\Assistant\294100\2519492373\1.6\Core")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate(root: Path) -> None:
    cat = load_catalog(root / "catalog")
    core = Path(os.environ.get("OBSIDIA_CORE", _DEFAULT_CORE))
    errors = validate_catalog(cat, scan_core_ranged(core))
    if errors and os.environ.get("OE_CE_ALLOW_PARTIAL") != "1":
        for msg in errors:
            print(msg, file=sys.stderr)
        sys.exit(1)

    _write(root / "Defs" / "Ammo" / "OE_Ammo.xml", emit_ammo_xml(cat.families))
    _write(
        root / "Defs" / "RecipeDefs" / "OE_AmmoRecipes.xml",
        emit_recipe_xml(cat.families),
    )
    _write(
        root / "Patches" / "Weapons" / "OE_Ranged.xml",
        emit_gun_patches(cat.families),
    )
    _write(
        root / "Patches" / "Weapons" / "OE_Melee.xml",
        emit_melee_xml(cat.melee),
    )
    _write(
        root / "Patches" / "PawnKinds" / "OE_Loadouts.xml",
        emit_pawnkind_xml(core, cat.families),
    )
