from __future__ import annotations

from oe_ce.constants import RUNGS
from oe_ce.models import Member

MELEE_POWER_BY_RUNG: dict[str, int] = {
    "proto": 8,
    "odc_t1": 10,
    "odc_t2": 12,
    "odc_t3": 14,
    "odc_t4": 16,
    "otc": 9,
    "omc": 11,
    "oec": 12,
    "oe": 13,
    "omg": 18,
}

MELEE_POWER_BY_RUNG["occ"] = MELEE_POWER_BY_RUNG["odc_t1"]

for _alias in (
    "occ_reforge",
    "omc_mod",
    "oec_t2",
    "otc_t2",
    "cac_t1",
    "bio_t3",
):
    MELEE_POWER_BY_RUNG[_alias] = MELEE_POWER_BY_RUNG["odc_t3"]

for _alias in ("cac_t2", "bio_t4", "heroic", "trophy"):
    MELEE_POWER_BY_RUNG[_alias] = MELEE_POWER_BY_RUNG["odc_t4"]

MELEE_POWER_BY_RUNG["mech"] = MELEE_POWER_BY_RUNG["omc"]

assert set(MELEE_POWER_BY_RUNG) == set(RUNGS)


def _tools_replace(member: Member) -> str:
    power = MELEE_POWER_BY_RUNG[member.rung]
    return f"""  <Operation Class="PatchOperationReplace">
    <xpath>Defs/ThingDef[defName="{member.def_name}"]/tools</xpath>
    <value>
      <tools>
        <li Class="CombatExtended.ToolCE">
          <label>handle</label>
          <capacities><li>Poke</li></capacities>
          <power>1</power>
          <chanceFactor>0.33</chanceFactor>
          <cooldownTime>1.26</cooldownTime>
        </li>
        <li Class="CombatExtended.ToolCE">
          <label>blade</label>
          <capacities><li>Cut</li></capacities>
          <power>{power}</power>
          <cooldownTime>1.18</cooldownTime>
        </li>
      </tools>
    </value>
  </Operation>"""


def emit_melee_xml(members: list[Member]) -> str:
    blocks = [_tools_replace(m) for m in sorted(members, key=lambda m: m.def_name)]
    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>'
