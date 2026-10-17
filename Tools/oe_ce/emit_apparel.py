from __future__ import annotations

from oe_ce.apparel_models import ApparelSet
from oe_ce.apparel_rungs import ARMOR, COVERAGE, apparel_stats
from oe_ce.emit_common import ensure_node, set_stat, thing_xpath
from oe_ce.scan_apparel import CoreApparel


def _partial_armor(def_name: str, template: str) -> str:
    rows: list[str] = []
    for row in COVERAGE[template]:
        parts = "\n".join(f"              <li>{part}</li>" for part in row.parts)
        for stat in ("ArmorRating_Sharp", "ArmorRating_Blunt"):
            rows.append(
                f"""          <li>
            <{stat}>{row.mult:.2f}</{stat}>
            <parts>
{parts}
            </parts>
          </li>"""
            )
    inner = "\n".join(rows)
    return f"""  <Operation Class="PatchOperationAddModExtension">
    <xpath>{thing_xpath(def_name)}</xpath>
    <value>
      <li Class="CombatExtended.PartialArmorExt">
        <stats>
{inner}
        </stats>
      </li>
    </value>
  </Operation>"""


def _member_ops(kind: str, def_name: str, rung: str, inherits_coverage: bool) -> list[str]:
    stats = apparel_stats(kind, rung)
    ops = [ensure_node(def_name, "statBases")]
    for stat, value in (
        ("ArmorRating_Sharp", stats.sharp),
        ("ArmorRating_Blunt", stats.blunt),
        ("ArmorRating_Heat", stats.heat),
        ("Mass", stats.mass),
        ("Bulk", stats.bulk),
        ("WornBulk", stats.worn_bulk),
    ):
        ops.append(set_stat(def_name, "statBases", stat, value))
    if kind == ARMOR and stats.carry_weight is not None and stats.carry_bulk is not None:
        ops.append(ensure_node(def_name, "equippedStatOffsets"))
        ops.append(set_stat(def_name, "equippedStatOffsets", "CarryWeight", stats.carry_weight))
        ops.append(set_stat(def_name, "equippedStatOffsets", "CarryBulk", stats.carry_bulk))
    if not inherits_coverage:
        ops.append(_partial_armor(def_name, stats.template))
    return ops


def emit_apparel_xml(sets: list[ApparelSet], kind: str, core: dict[str, CoreApparel]) -> str:
    catalogued = {m.def_name for s in sets for m in s.members}
    rows = sorted((m.def_name, s.member_rung(m)) for s in sets for m in s.members)
    blocks: list[str] = []
    for def_name, rung in rows:
        info = core.get(def_name)
        inherits = info is not None and info.concrete_parent in catalogued
        blocks.extend(_member_ops(kind, def_name, rung, inherits))
    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>\n'
