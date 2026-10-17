from __future__ import annotations

import os
import sys
from pathlib import Path

from oe_ce.apparel_load import load_apparel_catalog
from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.constants import DEFAULT_OBSIDIA_BIOTECH, DEFAULT_OBSIDIA_CORE
from oe_ce.emit_ammo import emit_ammo_xml
from oe_ce.emit_apparel import emit_apparel_xml
from oe_ce.emit_guns import emit_gun_patches
from oe_ce.emit_melee import emit_melee_xml
from oe_ce.emit_pawnkinds import emit_pawnkind_xml
from oe_ce.emit_races import collect_race_tools, emit_race_xml
from oe_ce.emit_recipes import emit_recipe_xml
from oe_ce.load import load_catalog
from oe_ce.race_analogues import ANIMAL, MECHANOID
from oe_ce.race_load import load_race_catalog
from oe_ce.scan_apparel import scan_core_apparel
from oe_ce.scan_obsidia import scan_core_ranged
from oe_ce.scan_races import scan_races
from oe_ce.validate import validate_catalog
from oe_ce.validate_apparel import validate_apparel_catalog
from oe_ce.validate_races import validate_race_catalog


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _require_core_dirs(core: Path) -> None:
    weapons = core / "Defs" / "ThingDefs_Misc" / "Weapons"
    pawnkinds = core / "Defs" / "PawnKinds"
    apparel = core / "Defs" / "ThingDefs_Misc" / "Apparel"
    races = core / "Defs" / "ThingDefs_Races"
    if not weapons.is_dir():
        raise FileNotFoundError(f"Obsidia Core weapons dir missing: {weapons}")
    if not pawnkinds.is_dir():
        raise FileNotFoundError(f"Obsidia Core PawnKinds dir missing: {pawnkinds}")
    if not apparel.is_dir():
        raise FileNotFoundError(f"Obsidia Core apparel dir missing: {apparel}")
    if not races.is_dir():
        raise FileNotFoundError(f"Obsidia Core races dir missing: {races}")


def generate(root: Path) -> None:
    cat = load_catalog(root / "catalog")
    apparel = load_apparel_catalog(root / "catalog")
    races = load_race_catalog(root / "catalog")
    core = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))
    _require_core_dirs(core)
    core_apparel = scan_core_apparel(core)
    errors = validate_catalog(cat, scan_core_ranged(core))
    errors += validate_apparel_catalog(apparel, core_apparel)
    biotech = Path(os.environ.get("OBSIDIA_BIOTECH", DEFAULT_OBSIDIA_BIOTECH))
    bio = biotech if biotech.is_dir() else None
    core_races = scan_races(core, bio)
    errors += validate_race_catalog(races, core_races)
    if errors and os.environ.get("OE_CE_ALLOW_PARTIAL") != "1":
        for msg in errors:
            print(msg, file=sys.stderr)
        sys.exit(1)

    _write(root / "Defs" / "Ammo" / "OE_Ammo.xml", emit_ammo_xml(cat.families, core))
    _write(
        root / "Defs" / "RecipeDefs" / "OE_AmmoRecipes.xml",
        emit_recipe_xml(cat.families),
    )
    _write(
        root / "Patches" / "Weapons" / "OE_Ranged.xml",
        emit_gun_patches(cat.families, core),
    )
    _write(
        root / "Patches" / "Weapons" / "OE_Melee.xml",
        emit_melee_xml(cat.melee),
    )
    _write(
        root / "Patches" / "PawnKinds" / "OE_Loadouts.xml",
        emit_pawnkind_xml(core, cat.families),
    )
    _write(
        root / "Patches" / "Apparel" / "OE_Armor.xml",
        emit_apparel_xml(apparel.armor, ARMOR, core_apparel),
    )
    _write(
        root / "Patches" / "Apparel" / "OE_Helmets.xml",
        emit_apparel_xml(apparel.helmets, HELMET, core_apparel),
    )
    race_tools = collect_race_tools(core, bio)
    _write(
        root / "Patches" / "Races" / "OE_Animals.xml",
        emit_race_xml(races.sets, ANIMAL, core_races, race_tools),
    )
    _write(
        root / "Patches" / "Races" / "OE_Mechanoids.xml",
        emit_race_xml(races.sets, MECHANOID, core_races, race_tools),
    )
