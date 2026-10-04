from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from oe_ce.constants import RANGED_SCAN_EXCLUDE


def _iter_weapon_xml(core: Path) -> list[Path]:
    root = core / "Defs" / "ThingDefs_Misc" / "Weapons"
    if not root.is_dir():
        raise FileNotFoundError(f"Obsidia Core weapons dir missing: {root}")
    return sorted(root.rglob("*.xml"))


def _thingdefs(path: Path) -> list[ET.Element]:
    tree = ET.parse(path)
    return list(tree.getroot())


def scan_core_ranged(core: Path) -> set[str]:
    names: set[str] = set()
    for path in _iter_weapon_xml(core):
        for el in _thingdefs(path):
            if el.tag != "ThingDef":
                continue
            if el.get("Abstract") == "True":
                continue
            def_el = el.find("defName")
            if def_el is None or not def_el.text:
                continue
            if el.find("verbs") is None:
                continue
            name = def_el.text.strip()
            if name in RANGED_SCAN_EXCLUDE:
                continue
            names.add(name)
    return names


def scan_core_melee(core: Path) -> set[str]:
    names: set[str] = set()
    for path in _iter_weapon_xml(core):
        for el in _thingdefs(path):
            if el.tag != "ThingDef" or el.get("Abstract") == "True":
                continue
            def_el = el.find("defName")
            if def_el is None or not def_el.text:
                continue
            name = def_el.text.strip()
            if el.find("verbs") is not None:
                if name in RANGED_SCAN_EXCLUDE:
                    names.add(name)
                continue
            if el.find("tools") is None:
                continue
            names.add(name)
    return names


def thing_def_has_tools(core: Path, def_name: str) -> bool:
    for path in _iter_weapon_xml(core):
        for el in _thingdefs(path):
            if el.tag != "ThingDef":
                continue
            def_el = el.find("defName")
            if def_el is None or (def_el.text or "").strip() != def_name:
                continue
            return el.find("tools") is not None
    return False


def weapon_tags(core: Path, def_name: str) -> list[str]:
    for path in _iter_weapon_xml(core):
        for el in _thingdefs(path):
            def_el = el.find("defName")
            if def_el is None or (def_el.text or "").strip() != def_name:
                continue
            tags = el.find("weaponTags")
            if tags is None:
                return []
            return [(li.text or "").strip() for li in tags.findall("li") if li.text]
    return []
