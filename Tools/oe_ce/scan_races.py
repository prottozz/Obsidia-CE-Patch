from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from oe_ce.race_analogues import ANIMAL, MECHANOID
from oe_ce.scan_obsidia import ThingDefIndex, index_thingdefs, walk_parents


@dataclass(frozen=True)
class CoreRace:
    def_name: str
    kind: str
    concrete_parent: str | None = None


def _races_dir(root: Path, label: str) -> Path:
    path = root / "Defs" / "ThingDefs_Races"
    if not path.is_dir():
        raise FileNotFoundError(f"Obsidia {label} races dir missing: {path}")
    return path


def _has_race(index: ThingDefIndex, el: ET.Element) -> bool:
    return any(node.find("race") is not None for node in walk_parents(index, el))


def _flesh_type(index: ThingDefIndex, el: ET.Element) -> str | None:
    for node in walk_parents(index, el):
        text = node.findtext("race/fleshType")
        if text and text.strip():
            return text.strip()
    return None


def _kind(index: ThingDefIndex, el: ET.Element, def_name: str) -> str:
    if _flesh_type(index, el) == "Mechanoid" or def_name.startswith("OE_Mech_"):
        return MECHANOID
    return ANIMAL


def _concrete_parent(index: ThingDefIndex, el: ET.Element) -> str | None:
    parent_name = el.get("ParentName")
    if not parent_name:
        return None
    parent = index.by_name.get(parent_name)
    if parent is None or parent.get("Abstract") == "True":
        return None
    return (parent.findtext("defName") or "").strip() or None


def _collect(index: ThingDefIndex) -> dict[str, CoreRace]:
    out: dict[str, CoreRace] = {}
    for def_name, el in index.by_def.items():
        if el.get("Abstract") == "True":
            continue
        if not _has_race(index, el):
            continue
        out[def_name] = CoreRace(def_name, _kind(index, el, def_name), _concrete_parent(index, el))
    return out


def _optional_race_xmls(root: Path | None) -> list[Path]:
    if root is None:
        return []
    races = root / "Defs" / "ThingDefs_Races"
    if not races.is_dir():
        return []
    return sorted(races.rglob("*.xml"))


def scan_races(
    core: Path,
    biotech: Path | None = None,
    anomaly: Path | None = None,
    ideology: Path | None = None,
    royalty: Path | None = None,
) -> dict[str, CoreRace]:
    xml_paths = sorted(_races_dir(core, "Core").rglob("*.xml"))
    for root in (biotech, anomaly, ideology, royalty):
        xml_paths.extend(_optional_race_xmls(root))
    return _collect(index_thingdefs(xml_paths))
