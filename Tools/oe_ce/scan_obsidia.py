from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


def _iter_weapon_xml(core: Path) -> list[Path]:
    root = core / "Defs" / "ThingDefs_Misc" / "Weapons"
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
            names.add(def_el.text.strip())
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
            if el.find("verbs") is not None:
                continue
            if el.find("tools") is None:
                continue
            names.add(def_el.text.strip())
    return names


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
