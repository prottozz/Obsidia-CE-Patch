from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from oe_ce.models import Family, Member
from oe_ce.scan_obsidia import weapon_tags


def _pawn_kind_defs(core: Path) -> list[tuple[str, list[str]]]:
    root = core / "Defs" / "PawnKinds"
    out: list[tuple[str, list[str]]] = []
    for path in sorted(root.rglob("*.xml")):
        tree = ET.parse(path)
        for el in tree.getroot():
            if el.tag != "PawnKindDef":
                continue
            def_el = el.find("defName")
            if def_el is None or not def_el.text:
                continue
            tags_el = el.find("weaponTags")
            tags: list[str] = []
            if tags_el is not None:
                tags = [
                    (li.text or "").strip()
                    for li in tags_el.findall("li")
                    if (li.text or "").strip()
                ]
            out.append((def_el.text.strip(), tags))
    return out


def _loadout_op(def_name: str, min_mag: int, max_mag: int) -> str:
    return f"""  <Operation Class="PatchOperationAddModExtension">
    <xpath>Defs/PawnKindDef[defName="{def_name}"]</xpath>
    <value>
      <li Class="CombatExtended.LoadoutPropertiesExtension">
        <primaryMagazineCount>
          <min>{min_mag}</min>
          <max>{max_mag}</max>
        </primaryMagazineCount>
      </li>
    </value>
  </Operation>"""


def emit_pawnkind_xml(core: Path, families: list[Family]) -> str:
    tag_members: dict[str, list[Member]] = {}
    for fam in families:
        for member in fam.members:
            for tag in weapon_tags(core, member.def_name):
                tag_members.setdefault(tag, []).append(member)

    catalog_tags = set(tag_members)
    blocks: list[str] = []
    for def_name, kind_tags in sorted(_pawn_kind_defs(core), key=lambda row: row[0]):
        hit = catalog_tags.intersection(kind_tags)
        if not hit:
            continue
        members: list[Member] = []
        for tag in hit:
            members.extend(tag_members[tag])
        ap_npc = any(m.ap_npc for m in members)
        min_mag, max_mag = (10, 20) if ap_npc else (8, 16)
        blocks.append(_loadout_op(def_name, min_mag, max_mag))

    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>'
