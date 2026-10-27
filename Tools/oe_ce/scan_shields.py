from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from oe_ce.scan_obsidia import ThingDefIndex, walk_parents

WORN = "worn"
HANDHELD = "handheld"
INNATE = "innate"
UPGRADE = "upgrade"

VANILLA_SHIELD = "CompProperties_Shield"
VEF_SHIELD = "VEF.Apparels.CompProperties_Shield"
VEF_THINGCLASS = "VEF.Apparels.Apparel_Shield"
_DEFNAME_RE = re.compile(r'ThingDef\[defName="([^"]+)"\]')


@dataclass(frozen=True)
class CoreShield:
    def_name: str
    kind: str
    blocks_ranged: bool | None = None
    concrete_parent: str | None = None
    tex_path: str | None = None


def _parse(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def _xml_paths(root: Path | None) -> list[Path]:
    if root is None or not root.is_dir():
        return []
    return sorted(root.rglob("*.xml"))


def _index_thingdefs(paths: list[Path]) -> ThingDefIndex:
    by_def: dict[str, ET.Element] = {}
    by_name: dict[str, ET.Element] = {}
    for path in paths:
        root = _parse(path)
        if root is None:
            continue
        for el in root.iter("ThingDef"):
            def_el = el.find("defName")
            if def_el is not None and (def_el.text or "").strip():
                by_def[def_el.text.strip()] = el
            name = el.get("Name")
            if name:
                by_name[name] = el
    return ThingDefIndex(by_def=by_def, by_name=by_name)


def _is_abstract(el: ET.Element) -> bool:
    return (el.get("Abstract") or "").lower() == "true"


def _concrete_parent(index: ThingDefIndex, el: ET.Element) -> str | None:
    parent_name = el.get("ParentName")
    if not parent_name:
        return None
    parent = index.by_name.get(parent_name) or index.by_def.get(parent_name)
    if parent is None or _is_abstract(parent):
        return None
    return (parent.findtext("defName") or "").strip() or None


def _inherited_comps(index: ThingDefIndex, el: ET.Element) -> list[ET.Element]:
    comps: list[ET.Element] = []
    for node in walk_parents(index, el):
        found = node.find("comps")
        if found is None:
            continue
        comps.extend(found.findall("li"))
    return comps


def _inherited_text(index: ThingDefIndex, el: ET.Element, xpath: str) -> str | None:
    tags = xpath.split("/")
    for node in walk_parents(index, el):
        current: ET.Element | None = node
        for tag in tags:
            if current is None:
                break
            current = current.find(tag)
        if current is not None and (current.text or "").strip():
            return current.text.strip()
    return None


def _blocks_ranged(index: ThingDefIndex, el: ET.Element) -> bool | None:
    for li in _inherited_comps(index, el):
        if li.get("Class") == VANILLA_SHIELD:
            text = (li.findtext("blocksRangedWeapons") or "").strip().lower()
            if text == "true":
                return True
            if text == "false":
                return False
            return None
    return None


def _has_race(index: ThingDefIndex, el: ET.Element) -> bool:
    return any(node.find("race") is not None for node in walk_parents(index, el))


def _classify(index: ThingDefIndex, el: ET.Element, def_name: str) -> str | None:
    comps = {li.get("Class") for li in _inherited_comps(index, el)}
    thing_class = _inherited_text(index, el, "thingClass")
    if VEF_SHIELD in comps or thing_class == VEF_THINGCLASS:
        return HANDHELD
    if VANILLA_SHIELD in comps:
        return WORN
    energy = _inherited_text(index, el, "statBases/EnergyShieldEnergyMax")
    if energy and (_has_race(index, el) or def_name.startswith("OE_Mech_")):
        return INNATE
    return None


def _patched_energy_names(paths: list[Path]) -> set[str]:
    names: set[str] = set()
    for path in paths:
        root = _parse(path)
        if root is None:
            continue
        for el in root.iter():
            xpath_el = el.find("xpath")
            if xpath_el is None or not (xpath_el.text or "").strip():
                continue
            blob = ET.tostring(el, encoding="unicode")
            if "EnergyShieldEnergyMax" not in blob:
                continue
            names.update(_DEFNAME_RE.findall(xpath_el.text))
    return names


def _collect_thingdefs(
    index: ThingDefIndex,
    out: dict[str, CoreShield],
) -> None:
    for def_name, el in index.by_def.items():
        if _is_abstract(el):
            continue
        kind = _classify(index, el, def_name)
        if kind is None:
            continue
        out[def_name] = CoreShield(
            def_name=def_name,
            kind=kind,
            blocks_ranged=_blocks_ranged(index, el) if kind == WORN else None,
            concrete_parent=_concrete_parent(index, el),
            tex_path=_inherited_text(index, el, "graphicData/texPath"),
        )


def _collect_upgrades(paths: list[Path], out: dict[str, CoreShield]) -> None:
    for path in paths:
        root = _parse(path)
        if root is None:
            continue
        for el in root.iter("MU.MechUpgradeDef"):
            if _is_abstract(el):
                continue
            def_name = (el.findtext("defName") or "").strip()
            if not def_name:
                continue
            factor = el.findtext("statFactors/EnergyShieldEnergyMax")
            if not factor:
                continue
            out[def_name] = CoreShield(def_name, UPGRADE)


def scan_shields(
    core: Path,
    royalty: Path | None = None,
    vef: Path | None = None,
    biotech: Path | None = None,
    mech_upgrades: Path | None = None,
    anomaly: Path | None = None,
    odyssey: Path | None = None,
) -> dict[str, CoreShield]:
    apparel = _xml_paths(core / "Defs" / "ThingDefs_Misc" / "Apparel")
    races = _xml_paths(core / "Defs" / "ThingDefs_Races")
    royalty_paths = _xml_paths(royalty / "Defs" if royalty is not None else None)
    vef_paths = _xml_paths(vef)
    bio_defs = _xml_paths(biotech / "Defs" if biotech is not None else None)
    bio_patches = _xml_paths(biotech / "Patches" if biotech is not None else None)
    mu_paths = _xml_paths(mech_upgrades)
    anomaly_defs = _xml_paths(anomaly / "Defs" if anomaly is not None else None)
    odyssey_defs = _xml_paths(odyssey / "Defs" if odyssey is not None else None)

    index = _index_thingdefs(
        apparel + races + royalty_paths + vef_paths + bio_defs + anomaly_defs + odyssey_defs
    )
    out: dict[str, CoreShield] = {}
    _collect_thingdefs(index, out)
    for name in _patched_energy_names(bio_patches):
        out.setdefault(name, CoreShield(name, INNATE))
    _collect_upgrades(mu_paths, out)
    return out
