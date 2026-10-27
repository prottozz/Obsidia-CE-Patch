"""Obsidia turret buildings and the turret guns they mount.

Turret buildings and guns live in ThingDefs_Buildings, except the EGO deployable
turret, whose gun and building sit in the Biotech apparel file. Every tree's
Defs folder is indexed together so DLC defs resolve Core parents.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from oe_ce.constants import (
    ANOMALY_PACKAGE,
    BIOTECH_PACKAGE,
    ODYSSEY_PACKAGE,
    ROYALTY_PACKAGE,
)
from oe_ce.scan_obsidia import ThingDefIndex, walk_parents

AMMO_KIT = "OE_AmmoKit"
REFUELABLE = "CompProperties_Refuelable"
EXPLOSIVE = "CompProperties_Explosive"


@dataclass(frozen=True)
class ScannedTurret:
    def_name: str
    gun: str
    package: str | None
    fuel_capacity: float | None  # None when the turret has no OE_AmmoKit refuel
    kit_shots: float | None  # Obsidia fuelMultiplier: shots per kit
    tactical: bool  # deployed by turret-pack apparel (parent BuildingBase, no frame)
    explosive: bool


@dataclass(frozen=True)
class ScannedTurretGun:
    def_name: str
    package: str | None
    projectile: str | None
    burst: int | None


@dataclass
class TurretScan:
    turrets: dict[str, ScannedTurret]
    guns: dict[str, ScannedTurretGun]
    index: ThingDefIndex


def _defs_files(root: Path | None) -> list[Path]:
    if root is None:
        return []
    defs = root / "Defs"
    return sorted(defs.rglob("*.xml")) if defs.is_dir() else []


def _parse(path: Path) -> list[ET.Element]:
    try:
        return list(ET.parse(path).getroot())
    except (ET.ParseError, OSError):
        return []


def _inherited(index: ThingDefIndex, el: ET.Element, path: str) -> ET.Element | None:
    for node in walk_parents(index, el):
        found = node.find(path)
        if found is not None:
            return found
    return None


def _inherited_text(index: ThingDefIndex, el: ET.Element, path: str) -> str | None:
    found = _inherited(index, el, path)
    if found is None or not (found.text or "").strip():
        return None
    return found.text.strip()


def _comp(index: ThingDefIndex, el: ET.Element, cls: str) -> ET.Element | None:
    for node in walk_parents(index, el):
        comps = node.find("comps")
        if comps is None:
            continue
        for li in comps.findall("li"):
            if li.get("Class") == cls:
                return li
    return None


def _number(text: str | None) -> float | None:
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def scan_turrets(
    core: Path,
    royalty: Path | None = None,
    *,
    biotech: Path | None = None,
    anomaly: Path | None = None,
    odyssey: Path | None = None,
) -> TurretScan:
    trees: list[tuple[Path | None, str | None]] = [
        (core, None),
        (royalty, ROYALTY_PACKAGE),
        (biotech, BIOTECH_PACKAGE),
        (anomaly, ANOMALY_PACKAGE),
        (odyssey, ODYSSEY_PACKAGE),
    ]
    by_def: dict[str, ET.Element] = {}
    by_name: dict[str, ET.Element] = {}
    package_of: dict[str, str | None] = {}
    for root, pkg in trees:
        for path in _defs_files(root):
            for el in _parse(path):
                if el.tag != "ThingDef":
                    continue
                name = (el.findtext("defName") or "").strip()
                if name:
                    by_def[name] = el
                    package_of[name] = pkg
                if el.get("Name"):
                    by_name[el.get("Name")] = el
    index = ThingDefIndex(by_def=by_def, by_name=by_name)

    turrets: dict[str, ScannedTurret] = {}
    guns: dict[str, ScannedTurretGun] = {}
    for name, el in sorted(by_def.items()):
        if el.get("Abstract") == "True":
            continue
        gun = _inherited_text(index, el, "building/turretGunDef")
        if not gun:
            continue
        refuel = _comp(index, el, REFUELABLE)
        capacity = kit_shots = None
        if refuel is not None:
            fuels = [(li.text or "").strip() for li in refuel.findall("fuelFilter/thingDefs/li")]
            if AMMO_KIT in fuels:
                capacity = _number(refuel.findtext("fuelCapacity"))
                kit_shots = _number(refuel.findtext("fuelMultiplier")) or 1.0
        turrets[name] = ScannedTurret(
            def_name=name,
            gun=gun,
            package=package_of.get(name),
            fuel_capacity=capacity,
            kit_shots=kit_shots,
            tactical=el.get("ParentName") == "BuildingBase",
            explosive=_comp(index, el, EXPLOSIVE) is not None,
        )
        gun_el = by_def.get(gun)
        if gun_el is not None and gun not in guns:
            burst = _number(_inherited_text(index, gun_el, "verbs/li/burstShotCount"))
            guns[gun] = ScannedTurretGun(
                def_name=gun,
                package=package_of.get(gun),
                projectile=_inherited_text(index, gun_el, "verbs/li/defaultProjectile"),
                burst=int(burst) if burst else None,
            )
    return TurretScan(turrets=turrets, guns=guns, index=index)
