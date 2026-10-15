from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from oe_ce.apparel_rungs import ARMOR, HELMET
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


def _apparel_dir(core: Path) -> Path:
    root = core / "Defs" / "ThingDefs_Misc" / "Apparel"
    if not root.is_dir():
        raise FileNotFoundError(f"Obsidia Core apparel dir missing: {root}")
    return root


def _index(core: Path) -> ThingDefIndex:
    return index_thingdefs(sorted(_apparel_dir(core).rglob("*.xml")))


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


def scan_core_apparel(core: Path) -> dict[str, CoreApparel]:
    index = _index(core)
    out: dict[str, CoreApparel] = {}
    for def_name, el in sorted(index.by_def.items()):
        if el.get("Abstract") == "True" or is_excluded_apparel(def_name):
            continue
        kind = _kind(_layers(index, el))
        if kind is None:
            continue
        out[def_name] = CoreApparel(def_name, kind, _concrete_parent(index, el))
    return out
