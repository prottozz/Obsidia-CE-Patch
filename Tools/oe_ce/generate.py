from __future__ import annotations

import os
import sys
from pathlib import Path

from oe_ce.apparel_load import load_apparel_catalog
from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.constants import (
    ANOMALY_PACKAGE,
    BIOTECH_PACKAGE,
    DEFAULT_OBSIDIA_ANOMALY,
    DEFAULT_OBSIDIA_BIOTECH,
    DEFAULT_OBSIDIA_CORE,
    DEFAULT_OBSIDIA_IDEOLOGY,
    DEFAULT_OBSIDIA_MU,
    DEFAULT_OBSIDIA_ROYALTY,
    DEFAULT_OBSIDIA_VEF,
    GAME_VERSION,
    IDEOLOGY_PACKAGE,
    ROYALTY_PACKAGE,
)
from oe_ce.emit_ammo import emit_ammo_xml
from oe_ce.emit_apparel import emit_apparel_xml
from oe_ce.emit_grenade_belts import emit_grenade_belt_xml
from oe_ce.emit_guns import emit_gun_patches
from oe_ce.emit_melee import emit_melee_xml
from oe_ce.emit_pawnkinds import emit_pawnkind_xml
from oe_ce.emit_bodies import ANIMAL as BODY_ANIMAL
from oe_ce.emit_bodies import MECHANOID as BODY_MECHANOID
from oe_ce.emit_bodies import emit_body_xml
from oe_ce.emit_races import collect_race_tools, emit_race_xml
from oe_ce.emit_recipes import emit_recipe_xml
from oe_ce.emit_shields import emit_innate_xml, emit_upgrade_xml, emit_worn_handheld_xml
from oe_ce.body_load import load_body_catalog
from oe_ce.load import load_catalog
from oe_ce.race_analogues import ANIMAL, MECHANOID
from oe_ce.race_load import load_race_catalog
from oe_ce.scan_apparel import scan_core_apparel, scan_isolated_grenadiers
from oe_ce.scan_bodies import scan_bodies
from oe_ce.scan_obsidia import scan_core_ranged
from oe_ce.scan_races import scan_races
from oe_ce.scan_shields import scan_shields
from oe_ce.shield_load import load_shield_catalog
from oe_ce.validate import validate_catalog
from oe_ce.validate_bodies import validate_body_catalog
from oe_ce.validate_apparel import validate_apparel_catalog
from oe_ce.validate_races import validate_race_catalog
from oe_ce.validate_shields import validate_shield_catalog


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
    core_bodies = core / "Defs" / "Bodies"
    if not core_bodies.is_dir():
        raise FileNotFoundError(f"Obsidia Core bodies dir missing: {core_bodies}")


def _optional_dir(env_name: str, default: str) -> Path | None:
    path = Path(os.environ.get(env_name, default))
    return path if path.is_dir() else None


def generate(root: Path) -> None:
    cat = load_catalog(root / "catalog")
    apparel = load_apparel_catalog(root / "catalog")
    races = load_race_catalog(root / "catalog")
    shields = load_shield_catalog(root / "catalog")
    bodies = load_body_catalog(root / "catalog")
    core = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))
    _require_core_dirs(core)
    bio = _optional_dir("OBSIDIA_BIOTECH", DEFAULT_OBSIDIA_BIOTECH)
    anomaly = _optional_dir("OBSIDIA_ANOMALY", DEFAULT_OBSIDIA_ANOMALY)
    ideology = _optional_dir("OBSIDIA_IDEOLOGY", DEFAULT_OBSIDIA_IDEOLOGY)
    royalty = _optional_dir("OBSIDIA_ROYALTY", DEFAULT_OBSIDIA_ROYALTY)
    vef = _optional_dir("OBSIDIA_VEF", DEFAULT_OBSIDIA_VEF)
    mu = _optional_dir("OBSIDIA_MU", DEFAULT_OBSIDIA_MU)
    core_apparel = scan_core_apparel(core, royalty)
    isolated_grenadiers = scan_isolated_grenadiers(core, royalty)
    errors = validate_catalog(cat, scan_core_ranged(core))
    errors += validate_apparel_catalog(apparel, core_apparel)
    core_races = scan_races(core, bio, anomaly, ideology, royalty)
    present_packages = frozenset(
        pkg
        for path, pkg in (
            (bio, BIOTECH_PACKAGE),
            (anomaly, ANOMALY_PACKAGE),
            (ideology, IDEOLOGY_PACKAGE),
            (royalty, ROYALTY_PACKAGE),
        )
        if path is not None
    )
    errors += validate_race_catalog(races, core_races, present_packages=present_packages)
    scanned_bodies = scan_bodies(core, bio, anomaly)
    errors += validate_body_catalog(bodies, scanned_bodies, present_packages=present_packages)
    armor_names = {m.def_name for s in apparel.armor for m in s.members}
    scanned_shields = scan_shields(core, royalty, vef, bio, mu)
    errors += validate_shield_catalog(shields, scanned_shields, armor_names)
    if errors and os.environ.get("OE_CE_ALLOW_PARTIAL") != "1":
        for msg in errors:
            print(msg, file=sys.stderr)
        sys.exit(1)

    out = root / GAME_VERSION
    _write(out / "Defs" / "Ammo" / "OE_Ammo.xml", emit_ammo_xml(cat.families, core))
    _write(
        out / "Defs" / "RecipeDefs" / "OE_AmmoRecipes.xml",
        emit_recipe_xml(cat.families),
    )
    _write(
        out / "Patches" / "Weapons" / "OE_Ranged.xml",
        emit_gun_patches(cat.families, core),
    )
    _write(
        out / "Patches" / "Weapons" / "OE_Melee.xml",
        emit_melee_xml(cat.melee),
    )
    _write(
        out / "Patches" / "PawnKinds" / "OE_Loadouts.xml",
        emit_pawnkind_xml(core, cat.families),
    )
    _write(
        out / "Patches" / "Apparel" / "OE_Armor.xml",
        emit_apparel_xml(apparel.armor, ARMOR, core_apparel, isolated_grenadiers),
    )
    _write(
        out / "Patches" / "Apparel" / "OE_Helmets.xml",
        emit_apparel_xml(apparel.helmets, HELMET, core_apparel, isolated_grenadiers),
    )
    _write(
        out / "Patches" / "Apparel" / "OE_GrenadeBelts.xml",
        emit_grenade_belt_xml(),
    )
    race_tools = collect_race_tools(core, bio, anomaly, ideology, royalty)
    _write(
        out / "Patches" / "Races" / "OE_Animals.xml",
        emit_race_xml(races.sets, ANIMAL, core_races, race_tools),
    )
    _write(
        out / "Patches" / "Races" / "OE_Mechanoids.xml",
        emit_race_xml(races.sets, MECHANOID, core_races, race_tools),
    )
    _write(
        out / "Patches" / "Bodies" / "OE_Animals.xml",
        emit_body_xml(bodies.bodies, scanned_bodies, BODY_ANIMAL),
    )
    _write(
        out / "Patches" / "Bodies" / "OE_Mechanoids.xml",
        emit_body_xml(bodies.bodies, scanned_bodies, BODY_MECHANOID),
    )
    _write(
        out / "Patches" / "Apparel" / "OE_Shields.xml",
        emit_worn_handheld_xml(shields, scanned_shields),
    )
    _write(
        out / "Patches" / "Races" / "OE_Shields.xml",
        emit_innate_xml(shields),
    )
    _write(
        out / "Patches" / "Misc" / "OE_MechUpgrades.xml",
        emit_upgrade_xml(shields),
    )
