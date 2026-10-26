from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class BodyPart:
    def_name: str | None
    custom_label: str | None
    depth: str | None
    groups: tuple[str, ...]
    xpath: str
    children: list[BodyPart]


@dataclass(frozen=True)
class ScannedBody:
    def_name: str
    parts: list[BodyPart]
    custom: bool


def _bodies_dir(root: Path, label: str) -> Path:
    path = root / "Defs" / "Bodies"
    if not path.is_dir():
        raise FileNotFoundError(f"Obsidia {label} bodies dir missing: {path}")
    return path


def _optional_body_xmls(root: Path | None) -> list[Path]:
    if root is None:
        return []
    bodies = root / "Defs" / "Bodies"
    if not bodies.is_dir():
        return []
    return sorted(bodies.rglob("*.xml"))


def _bodydefs(path: Path) -> list[ET.Element]:
    tree = ET.parse(path)
    return [el for el in tree.getroot() if el.tag == "BodyDef"]


def _groups(el: ET.Element) -> tuple[str, ...]:
    groups_el = el.find("groups")
    if groups_el is None:
        return ()
    return tuple(
        text
        for li in groups_el.findall("li")
        for text in [(li.text or "").strip()]
        if text
    )


def _depth(el: ET.Element) -> str | None:
    depth_el = el.find("depth")
    if depth_el is None or not (depth_el.text or "").strip():
        return None
    return depth_el.text.strip()


def _child_xpath(parent_xpath: str, li: ET.Element) -> str:
    custom_label = (li.findtext("customLabel") or "").strip()
    if custom_label:
        return f'{parent_xpath}/parts/li[customLabel="{custom_label}"]'
    def_name = (li.findtext("def") or "").strip()
    return f'{parent_xpath}/parts/li[def="{def_name}"]'


def _part_from_element(el: ET.Element, xpath: str) -> BodyPart:
    def_name = (el.findtext("def") or "").strip() or None
    custom_label = (el.findtext("customLabel") or "").strip() or None
    children: list[BodyPart] = []
    parts_el = el.find("parts")
    if parts_el is not None:
        for li in parts_el.findall("li"):
            if li.find("def") is None and li.find("customLabel") is None:
                continue
            children.append(_part_from_element(li, _child_xpath(xpath, li)))
    return BodyPart(
        def_name,
        custom_label,
        _depth(el),
        _groups(el),
        xpath,
        children,
    )


def _scanned_body(el: ET.Element) -> ScannedBody | None:
    if el.get("Abstract") == "True":
        return None
    def_name = (el.findtext("defName") or "").strip()
    if not def_name or not def_name.startswith("OE"):
        return None
    core = el.find("corePart")
    if core is None:
        return None
    core_part = _part_from_element(core, "corePart")
    return ScannedBody(def_name, [core_part], True)


def _collect(xml_paths: list[Path]) -> dict[str, ScannedBody]:
    out: dict[str, ScannedBody] = {}
    for path in xml_paths:
        for el in _bodydefs(path):
            scanned = _scanned_body(el)
            if scanned is not None:
                out[scanned.def_name] = scanned
    return out


def scan_bodies(
    core: Path,
    biotech: Path | None = None,
    anomaly: Path | None = None,
) -> dict[str, ScannedBody]:
    xml_paths = sorted(_bodies_dir(core, "Core").rglob("*.xml"))
    for root in (biotech, anomaly):
        xml_paths.extend(_optional_body_xmls(root))
    return _collect(xml_paths)
