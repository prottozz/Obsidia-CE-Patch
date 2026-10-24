from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.constants import ROYALTY_PACKAGE
from oe_ce.scan_obsidia import ThingDefIndex, index_thingdefs, walk_parents

APPAREL_EXCLUDE_EXACT = frozenset(
    {
        "OE_Uniform_Military",
        "OE_Uniform_Worker",
        "ODC_Helmet_Miner",
        "ODC_Helmet_Constructor",
        "ODC_Helmet_Medic",
        "ODC_Helmet_Trader",
        "ODC_Helmet_Beastmaster",
        "EGO_Helmet_Exohelm_Worker",
        "EGO_Armor_Shell_Worker",
    }
)
APPAREL_EXCLUDE_SUBSTRINGS = ("Shield", "Barrier", "Grenadier")
APPAREL_EXCLUDE_PREFIXES = ("Grenade_",)


def is_excluded_apparel(def_name: str) -> bool:
    if def_name in APPAREL_EXCLUDE_EXACT:
        return True
    if def_name.startswith(APPAREL_EXCLUDE_PREFIXES):
        return True
    return any(part in def_name for part in APPAREL_EXCLUDE_SUBSTRINGS)


@dataclass(frozen=True)
class CoreApparel:
    def_name: str
    kind: str
    concrete_parent: str | None = None


@dataclass(frozen=True)
class IsolatedApparel:
    def_name: str
    kind: str
    concrete_parent: str
    sharp: float
    blunt: float
    heat: float
    mass: float
    offsets: tuple[tuple[str, str], ...]
    may_require: str | None = None


def _apparel_files(mod_root: Path, *, required: bool) -> list[Path]:
    root = mod_root / "Defs" / "ThingDefs_Misc" / "Apparel"
    if not root.is_dir():
        if required:
            raise FileNotFoundError(f"Obsidia apparel dir missing: {root}")
        return []
    return sorted(root.rglob("*.xml"))


def _index(core: Path, royalty: Path | None = None) -> ThingDefIndex:
    files = _apparel_files(core, required=True)
    if royalty is not None:
        files = files + _apparel_files(royalty, required=True)
    return index_thingdefs(files)


def _layers(index: ThingDefIndex, el: ET.Element) -> list[str]:
    for node in walk_parents(index, el):
        layers = node.find("apparel/layers")
        if layers is not None:
            return [(li.text or "").strip() for li in layers.findall("li")]
    return []


def _kind(layers: list[str]) -> str | None:
    if "Shell" in layers:
        return ARMOR
    if "Overhead" in layers:
        return HELMET
    return None


def _concrete_parent(index: ThingDefIndex, el: ET.Element) -> str | None:
    parent_name = el.get("ParentName")
    if not parent_name:
        return None
    parent = index.by_name.get(parent_name)
    if parent is None or parent.get("Abstract") == "True":
        return None
    return (parent.findtext("defName") or "").strip() or None


def _inherited_stat(index: ThingDefIndex, el: ET.Element, node: str, stat: str) -> str | None:
    for parent in walk_parents(index, el):
        block = parent.find(node)
        if block is None:
            continue
        child = block.find(stat)
        if child is not None and (child.text or "").strip():
            return child.text.strip()
    return None


def _inherited_offsets(index: ThingDefIndex, el: ET.Element) -> tuple[tuple[str, str], ...]:
    merged: dict[str, str] = {}
    for parent in reversed(walk_parents(index, el)):
        block = parent.find("equippedStatOffsets")
        if block is None:
            continue
        if block.get("Inherit") == "False":
            merged.clear()
        for child in list(block):
            val = (child.text or "").strip()
            if child.tag and val:
                merged[child.tag] = val
    return tuple(merged.items())


def scan_isolated_grenadiers(
    core: Path, royalty: Path | None = None
) -> dict[str, IsolatedApparel]:
    index = _index(core, royalty)
    royalty_defs: set[str] = set()
    if royalty is not None:
        royalty_defs = set(
            index_thingdefs(_apparel_files(royalty, required=True)).by_def
        )
    out: dict[str, IsolatedApparel] = {}
    for def_name, el in sorted(index.by_def.items()):
        if "Grenadier" not in def_name or el.get("Abstract") == "True":
            continue
        parent = _concrete_parent(index, el)
        kind = _kind(_layers(index, el))
        if parent is None or kind is None:
            continue
        try:
            sharp = float(_inherited_stat(index, el, "statBases", "ArmorRating_Sharp") or "")
            blunt = float(_inherited_stat(index, el, "statBases", "ArmorRating_Blunt") or "")
            heat = float(_inherited_stat(index, el, "statBases", "ArmorRating_Heat") or "")
            mass = float(_inherited_stat(index, el, "statBases", "Mass") or "")
        except ValueError:
            continue
        out[def_name] = IsolatedApparel(
            def_name,
            kind,
            parent,
            sharp,
            blunt,
            heat,
            mass,
            _inherited_offsets(index, el),
            ROYALTY_PACKAGE if def_name in royalty_defs else None,
        )
    return out


def scan_core_apparel(
    core: Path, royalty: Path | None = None
) -> dict[str, CoreApparel]:
    index = _index(core, royalty)
    out: dict[str, CoreApparel] = {}
    for def_name, el in sorted(index.by_def.items()):
        if el.get("Abstract") == "True" or is_excluded_apparel(def_name):
            continue
        kind = _kind(_layers(index, el))
        if kind is None:
            continue
        out[def_name] = CoreApparel(def_name, kind, _concrete_parent(index, el))
    return out
