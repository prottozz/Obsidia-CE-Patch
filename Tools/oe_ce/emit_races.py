from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from oe_ce.constants import BIOTECH_PACKAGE
from oe_ce.emit_common import ensure_node, format_num, set_stat, thing_xpath, wrap_optional_def
from oe_ce.race_analogues import ANIMAL, MECHANOID, race_stats
from oe_ce.race_models import RaceMember, RaceSet, RaceTool
from oe_ce.scan_obsidia import index_thingdefs, walk_parents
from oe_ce.scan_races import BIOTECH_BOSSES, CoreRace

SHARP_CAPACITIES = frozenset({"Scratch", "Bite", "Cut", "Stab", "Poke"})
_HANDLED_TOOL_TAGS = frozenset(
    {"label", "capacities", "power", "cooldownTime", "linkedBodyPartsGroup", "armorPenetration"}
)


def convert_tool_element(li: ET.Element) -> RaceTool:
    capacities = tuple(
        (c.text or "").strip() for c in li.findall("capacities/li") if (c.text or "").strip()
    )
    ap_el = li.find("armorPenetration")
    sharp = blunt = None
    if ap_el is not None and (ap_el.text or "").strip():
        value = float(ap_el.text)
        if any(cap in SHARP_CAPACITIES for cap in capacities):
            sharp = value
        else:
            blunt = value
    extras = tuple(
        ET.tostring(child, encoding="unicode")
        for child in list(li)
        if child.tag not in _HANDLED_TOOL_TAGS
    )
    power = li.findtext("power")
    cooldown = li.findtext("cooldownTime")
    return RaceTool(
        label=(li.findtext("label") or None),
        capacities=capacities,
        linked_body_parts_group=(li.findtext("linkedBodyPartsGroup") or None),
        power=float(power) if power else None,
        cooldown_time=float(cooldown) if cooldown else None,
        armor_penetration_sharp=sharp,
        armor_penetration_blunt=blunt,
        extra_xml=extras,
    )


def collect_race_tools(core: Path, biotech: Path | None = None) -> dict[str, list[RaceTool]]:
    paths = sorted((core / "Defs" / "ThingDefs_Races").rglob("*.xml"))
    if biotech is not None:
        bio = biotech / "Defs" / "ThingDefs_Races"
        if bio.is_dir():
            paths += sorted(bio.rglob("*.xml"))
    index = index_thingdefs(paths)
    out: dict[str, list[RaceTool]] = {}
    for def_name, el in index.by_def.items():
        collected: list[RaceTool] = []
        for node in walk_parents(index, el):
            tools = node.find("tools")
            if tools is None:
                continue
            converted = [convert_tool_element(li) for li in tools.findall("li")]
            collected = converted + collected
        if collected:
            out[def_name] = collected
    return out


def _tool_xml(tool: RaceTool) -> str:
    lines = ['        <li Class="CombatExtended.ToolCE">']
    if tool.label:
        lines.append(f"          <label>{tool.label}</label>")
    if tool.capacities:
        inner = "\n".join(f"            <li>{c}</li>" for c in tool.capacities)
        lines.append(f"          <capacities>\n{inner}\n          </capacities>")
    if tool.power is not None:
        lines.append(f"          <power>{format_num(tool.power)}</power>")
    if tool.cooldown_time is not None:
        lines.append(f"          <cooldownTime>{format_num(tool.cooldown_time)}</cooldownTime>")
    if tool.linked_body_parts_group:
        lines.append(
            f"          <linkedBodyPartsGroup>{tool.linked_body_parts_group}</linkedBodyPartsGroup>"
        )
    if tool.armor_penetration_sharp is not None:
        lines.append(
            f"          <armorPenetrationSharp>{format_num(tool.armor_penetration_sharp)}</armorPenetrationSharp>"
        )
    if tool.armor_penetration_blunt is not None:
        lines.append(
            f"          <armorPenetrationBlunt>{format_num(tool.armor_penetration_blunt)}</armorPenetrationBlunt>"
        )
    for extra in tool.extra_xml:
        lines.append("          " + extra.strip())
    lines.append("        </li>")
    return "\n".join(lines)


def _tools_op(def_name: str, tools: list[RaceTool]) -> str:
    inner = "\n".join(_tool_xml(t) for t in tools)
    base = thing_xpath(def_name)
    return f"""  <Operation Class="PatchOperationConditional">
    <xpath>{base}/tools</xpath>
    <match Class="PatchOperationReplace">
      <xpath>{base}/tools</xpath>
      <value>
        <tools Inherit="False">
{inner}
        </tools>
      </value>
    </match>
    <nomatch Class="PatchOperationAdd">
      <xpath>{base}</xpath>
      <value>
        <tools Inherit="False">
{inner}
        </tools>
      </value>
    </nomatch>
  </Operation>"""


def _durability_xml(kind: str, durability: int) -> str:
    lines = [
        '        <li Class="CombatExtended.CompProperties_ArmorDurability">',
        f"          <Durability>{durability}</Durability>",
        "          <Regenerates>true</Regenerates>",
        f"          <RegenInterval>{600 if kind == ANIMAL else 1250}</RegenInterval>",
        "          <RegenValue>5</RegenValue>",
        "          <MinArmorPct>0.5</MinArmorPct>",
    ]
    if kind == MECHANOID:
        lines += [
            "          <Repairable>true</Repairable>",
            "          <RepairIngredients>",
            "            <Steel>5</Steel>",
            "            <Plasteel>5</Plasteel>",
            "          </RepairIngredients>",
            "          <RepairTime>300</RepairTime>",
            "          <RepairValue>200</RepairValue>",
        ]
    lines.append("        </li>")
    return "\n".join(lines)


def _include(member: RaceMember, kind: str, core: dict[str, CoreRace]) -> bool:
    info = core.get(member.def_name)
    if info is not None:
        return info.kind == kind
    return kind == MECHANOID and member.def_name in BIOTECH_BOSSES


def _extension_op(def_name: str, shape: str) -> str:
    return f"""  <Operation Class="PatchOperationAddModExtension">
    <xpath>{thing_xpath(def_name)}</xpath>
    <value>
      <li Class="CombatExtended.RacePropertiesExtensionCE">
        <bodyShape>{shape}</bodyShape>
      </li>
    </value>
  </Operation>"""


def _durability_ops(def_name: str, kind: str, durability: int) -> list[str]:
    return [
        ensure_node(def_name, "comps"),
        f"""  <Operation Class="PatchOperationAdd">
    <xpath>{thing_xpath(def_name)}/comps</xpath>
    <value>
{_durability_xml(kind, durability)}
    </value>
  </Operation>""",
    ]


def _wrap_biotech(ops: list[str], def_name: str) -> str:
    return wrap_optional_def(ops, BIOTECH_PACKAGE, def_name)


def emit_race_xml(
    sets: list[RaceSet],
    kind: str,
    core: dict[str, CoreRace],
    tools: dict[str, list[RaceTool]],
) -> str:
    catalogued = {m.def_name for s in sets for m in s.members}
    shapes = {m.def_name: s.member_body_shape(m) for s in sets for m in s.members}
    rows: list[tuple[str, RaceSet, RaceMember]] = []
    for race_set, member in ((s, m) for s in sets for m in s.members):
        if _include(member, kind, core):
            rows.append((member.def_name, race_set, member))
    rows.sort(key=lambda row: row[0])
    blocks: list[str] = []
    for name, race_set, member in rows:
        stats = race_stats(race_set.member_analogue(member))
        shape = race_set.member_body_shape(member)
        info = core.get(name)
        parent = info.concrete_parent if info is not None else None
        ops: list[str] = []
        inherit_parent = parent is not None and parent in catalogued
        if not (inherit_parent and shapes.get(parent) == shape):
            ops.append(_extension_op(name, shape))
        ops.append(ensure_node(name, "statBases"))
        ops.append(set_stat(name, "statBases", "ArmorRating_Sharp", stats.sharp))
        ops.append(set_stat(name, "statBases", "ArmorRating_Blunt", stats.blunt))
        if stats.heat is not None:
            ops.append(set_stat(name, "statBases", "ArmorRating_Heat", stats.heat))
        ops.append(set_stat(name, "statBases", "MeleeDodgeChance", stats.dodge))
        ops.append(set_stat(name, "statBases", "MeleeCritChance", stats.crit))
        ops.append(set_stat(name, "statBases", "MeleeParryChance", stats.parry))
        tool_rows = member.tools if member.tools is not None else tools.get(name, [])
        if tool_rows:
            ops.append(_tools_op(name, tool_rows))
        if not inherit_parent:
            ops.extend(_durability_ops(name, kind, stats.durability))
        if name in BIOTECH_BOSSES:
            blocks.append(_wrap_biotech(ops, name))
        else:
            blocks.extend(ops)
    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>\n'
