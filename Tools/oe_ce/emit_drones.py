"""Swarmling drones deployed by Odyssey Swarmling armor.

They inherit vanilla ``BaseDrone`` (which CE 1.7-Test already gives bodyShape,
Sharp 2 / Blunt 3, carry and melee stats) but override armor with vanilla
numbers and replace tools with vanilla ``Tool``. Patch them like CE's Drone_Wasp.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from oe_ce.constants import ODYSSEY_PACKAGE
from oe_ce.emit_common import ensure_node, set_stat, thing_xpath, wrap_optional_def


@dataclass(frozen=True)
class DroneStats:
    power: float
    cooldown: float
    ap_sharp: float
    ap_blunt: float


# CE Wasp: vanilla stinger 6 / 2.4 s -> 10 / 2.6 s, AP 16 / 8. Same mapping;
# OMG's Obsidia AP 0.30 vs CAC 0.25 keeps it a notch sharper.
DRONES: dict[str, DroneStats] = {
    "CAC_Swarmling_Drone": DroneStats(10, 2.2, 16, 8),
    "OMG_Swarmling_Drone": DroneStats(10, 2.2, 18, 9),
}
DRONE_SHARP = 2
DRONE_BLUNT = 3
_DROP_TOOL_TAGS = frozenset({"power", "cooldownTime", "armorPenetration"})

_DURABILITY = """      <li Class="CombatExtended.CompProperties_ArmorDurability">
        <Durability>150</Durability>
        <Regenerates>true</Regenerates>
        <RegenInterval>1250</RegenInterval>
        <RegenValue>5</RegenValue>
        <Repairable>true</Repairable>
        <RepairIngredients>
          <Steel>5</Steel>
          <Plasteel>5</Plasteel>
        </RepairIngredients>
        <RepairTime>300</RepairTime>
        <RepairValue>200</RepairValue>
        <MinArmorPct>0.5</MinArmorPct>
      </li>"""


@dataclass(frozen=True)
class ScannedDrone:
    def_name: str
    tools: ET.Element | None


def scan_drones(odyssey: Path | None) -> dict[str, ScannedDrone]:
    if odyssey is None:
        return {}
    root = odyssey / "Defs"
    out: dict[str, ScannedDrone] = {}
    for path in sorted(root.rglob("*.xml")) if root.is_dir() else []:
        for el in ET.parse(path).getroot():
            if el.tag != "ThingDef" or el.get("ParentName") != "BaseDrone":
                continue
            if el.get("Abstract") == "True":
                continue
            name = (el.findtext("defName") or "").strip()
            if name:
                out[name] = ScannedDrone(name, el.find("tools"))
    return out


def validate_drones(scanned: dict[str, ScannedDrone]) -> list[str]:
    errors = [f"{name}: Obsidia BaseDrone not in DRONES table" for name in sorted(set(scanned) - set(DRONES))]
    if scanned:
        errors += [f"{name}: DRONES entry not found in Odyssey" for name in sorted(set(DRONES) - set(scanned))]
    for name, drone in sorted(scanned.items()):
        if drone.tools is None or len(drone.tools.findall("li")) != 1:
            errors.append(f"{name}: expected exactly one Obsidia tool to convert")
    return errors


def _tool_xml(tools: ET.Element, stats: DroneStats) -> str:
    li = tools.findall("li")[0]
    rows: list[str] = []
    for child in li:
        if child.tag in _DROP_TOOL_TAGS:
            continue
        clean = copy.deepcopy(child)
        clean.tail = None
        ET.indent(clean, space="  ")
        rows.append(ET.tostring(clean, encoding="unicode").strip())
    for tag, value in (
        ("power", stats.power),
        ("cooldownTime", stats.cooldown),
        ("armorPenetrationSharp", stats.ap_sharp),
        ("armorPenetrationBlunt", stats.ap_blunt),
    ):
        rows.append(f"<{tag}>{value:g}</{tag}>")
    body = "\n".join("\n".join("          " + line for line in row.split("\n")) for row in rows)
    return f"""      <tools Inherit="False">
        <li Class="CombatExtended.ToolCE">
{body}
        </li>
      </tools>"""


def _drone_ops(drone: ScannedDrone) -> list[str]:
    name = drone.def_name
    stats = DRONES[name]
    base = thing_xpath(name)
    return [
        ensure_node(name, "statBases"),
        set_stat(name, "statBases", "ArmorRating_Sharp", DRONE_SHARP),
        set_stat(name, "statBases", "ArmorRating_Blunt", DRONE_BLUNT),
        f"""  <Operation Class="PatchOperationReplace">
    <xpath>{base}/tools</xpath>
    <value>
{_tool_xml(drone.tools, stats)}
    </value>
  </Operation>""",
        ensure_node(name, "comps"),
        f"""  <Operation Class="PatchOperationAdd">
    <xpath>{base}/comps</xpath>
    <value>
{_DURABILITY}
    </value>
  </Operation>""",
    ]


def emit_drone_xml(scanned: dict[str, ScannedDrone]) -> str:
    blocks = [
        wrap_optional_def(_drone_ops(drone), ODYSSEY_PACKAGE, name)
        for name, drone in sorted(scanned.items())
        if name in DRONES and drone.tools is not None
    ]
    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>\n'
