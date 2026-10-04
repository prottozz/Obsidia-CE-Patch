from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from oe_ce.constants import RANGED_SCAN_EXCLUDE


@dataclass(frozen=True)
class ProjectileGraphic:
    tex_path: str
    graphic_class: str
    draw_size: str | None = None


@dataclass
class ThingDefIndex:
    by_def: dict[str, ET.Element]
    by_name: dict[str, ET.Element]


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


def index_weapon_thingdefs(core: Path) -> ThingDefIndex:
    by_def: dict[str, ET.Element] = {}
    by_name: dict[str, ET.Element] = {}
    for path in _iter_weapon_xml(core):
        for el in _thingdefs(path):
            if el.tag != "ThingDef":
                continue
            def_el = el.find("defName")
            if def_el is not None and (def_el.text or "").strip():
                by_def[def_el.text.strip()] = el
            name = el.get("Name")
            if name:
                by_name[name] = el
    return ThingDefIndex(by_def=by_def, by_name=by_name)


def _lookup_thing(index: ThingDefIndex, key: str) -> ET.Element | None:
    return index.by_def.get(key) or index.by_name.get(key)


def _walk_parents(index: ThingDefIndex, start: ET.Element) -> list[ET.Element]:
    out: list[ET.Element] = []
    current: ET.Element | None = start
    seen: set[str] = set()
    while current is not None:
        ident = current.get("Name") or (current.findtext("defName") or "") or str(id(current))
        if ident in seen:
            break
        seen.add(ident)
        out.append(current)
        parent = current.get("ParentName")
        if not parent:
            break
        current = _lookup_thing(index, parent)
    return out


def _default_projectile(el: ET.Element) -> str | None:
    verbs = el.find("verbs")
    if verbs is None:
        return None
    for li in verbs.findall("li"):
        proj = li.find("defaultProjectile")
        if proj is not None and (proj.text or "").strip():
            return proj.text.strip()
    return None


def _graphic_from_el(el: ET.Element) -> ProjectileGraphic | None:
    graphic = el.find("graphicData")
    if graphic is None:
        return None
    tex = graphic.find("texPath")
    if tex is None or not (tex.text or "").strip():
        return None
    cls = graphic.find("graphicClass")
    draw = graphic.find("drawSize")
    return ProjectileGraphic(
        tex_path=tex.text.strip(),
        graphic_class=(cls.text.strip() if cls is not None and cls.text else "Graphic_Single"),
        draw_size=(draw.text.strip() if draw is not None and draw.text else None),
    )


def weapon_projectile_graphic(
    core: Path,
    gun_def: str,
    index: ThingDefIndex | None = None,
) -> ProjectileGraphic | None:
    idx = index or index_weapon_thingdefs(core)
    gun = idx.by_def.get(gun_def)
    if gun is None:
        return None
    proj_name: str | None = None
    for el in _walk_parents(idx, gun):
        proj_name = _default_projectile(el)
        if proj_name:
            break
    if not proj_name:
        return None
    proj = _lookup_thing(idx, proj_name)
    if proj is None:
        return None
    for el in _walk_parents(idx, proj):
        graphic = _graphic_from_el(el)
        if graphic is not None:
            return graphic
    return None
