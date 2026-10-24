from __future__ import annotations

from oe_ce.apparel_models import ApparelSet
from oe_ce.apparel_rungs import ARMOR, COVERAGE, apparel_stats
from oe_ce.emit_common import ensure_node, set_stat, thing_xpath, wrap_optional_def
from oe_ce.scan_apparel import CoreApparel, IsolatedApparel

# Obsidia put these wearer offsets in statBases; they never apply until moved.
_PSYCHIC_FROM_STATBASES = frozenset(
    {
        "ODC_Armor_Recon_Prestige",
        "ODC_Armor_Duelist_Prestige",
    }
)


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


def _remove_if_present(xpath: str) -> str:
    return f"""  <Operation Class="PatchOperationConditional">
    <xpath>{xpath}</xpath>
    <match Class="PatchOperationRemove">
      <xpath>{xpath}</xpath>
    </match>
    <nomatch Class="PatchOperationTest">
      <xpath>Defs</xpath>
    </nomatch>
  </Operation>"""


def member_ops(kind: str, def_name: str, rung: str, inherits_coverage: bool) -> list[str]:
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
    if def_name in _PSYCHIC_FROM_STATBASES:
        for stat in ("PsychicSensitivityOffset", "PsychicEntropyRecoveryRate"):
            ops.append(_remove_if_present(f"{thing_xpath(def_name)}/statBases/{stat}"))
        ops.append(ensure_node(def_name, "equippedStatOffsets"))
        ops.append(
            set_stat(def_name, "equippedStatOffsets", "PsychicSensitivityOffset", 0.20)
        )
        ops.append(
            set_stat(def_name, "equippedStatOffsets", "PsychicEntropyRecoveryRate", 0.083)
        )
    if not inherits_coverage:
        ops.append(_partial_armor(def_name, stats.template))
    return ops


def _replace_or_add_node(def_name: str, node: str, inner: str) -> str:
    base = thing_xpath(def_name)
    return f"""  <Operation Class="PatchOperationConditional">
    <xpath>{base}/{node}</xpath>
    <match Class="PatchOperationReplace">
      <xpath>{base}/{node}</xpath>
      <value>
{inner}
      </value>
    </match>
    <nomatch Class="PatchOperationAdd">
      <xpath>{base}</xpath>
      <value>
{inner}
      </value>
    </nomatch>
  </Operation>"""


def isolate_ops(iso: IsolatedApparel) -> list[str]:
    ops = [ensure_node(iso.def_name, "statBases")]
    for stat, value in (
        ("ArmorRating_Sharp", iso.sharp),
        ("ArmorRating_Blunt", iso.blunt),
        ("ArmorRating_Heat", iso.heat),
        ("Mass", iso.mass),
        ("Bulk", 0),
        ("WornBulk", 0),
    ):
        ops.append(set_stat(iso.def_name, "statBases", stat, value))
    offset_rows = "\n".join(
        f"          <{stat}>{value}</{stat}>" for stat, value in iso.offsets
    )
    offsets_xml = (
        f'        <equippedStatOffsets Inherit="False">\n{offset_rows}\n'
        f"        </equippedStatOffsets>"
        if offset_rows
        else '        <equippedStatOffsets Inherit="False" />'
    )
    ops.append(_replace_or_add_node(iso.def_name, "equippedStatOffsets", offsets_xml))
    ops.append(
        _replace_or_add_node(
            iso.def_name, "modExtensions", '        <modExtensions Inherit="False" />'
        )
    )
    return ops


def emit_apparel_xml(
    sets: list[ApparelSet],
    kind: str,
    core: dict[str, CoreApparel],
    isolated: dict[str, IsolatedApparel] | None = None,
) -> str:
    catalogued = {m.def_name for s in sets for m in s.members}
    rows = sorted(
        (m.def_name, s.member_rung(m), s.member_may_require(m))
        for s in sets
        for m in s.members
    )
    core_ops: list[str] = []
    optional: list[tuple[str, str, list[str]]] = []
    for def_name, rung, may_require in rows:
        info = core.get(def_name)
        inherits = info is not None and info.concrete_parent in catalogued
        ops = member_ops(kind, def_name, rung, inherits)
        if may_require:
            optional.append((may_require, def_name, ops))
        else:
            core_ops.extend(ops)
    for iso in sorted((isolated or {}).values(), key=lambda item: item.def_name):
        if iso.kind != kind or iso.concrete_parent not in catalogued:
            continue
        ops = isolate_ops(iso)
        if iso.may_require:
            optional.append((iso.may_require, iso.def_name, ops))
        else:
            core_ops.extend(ops)
    blocks = list(core_ops)
    for pkg, def_name, ops in optional:
        blocks.append(wrap_optional_def(ops, pkg, def_name))
    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>\n'
