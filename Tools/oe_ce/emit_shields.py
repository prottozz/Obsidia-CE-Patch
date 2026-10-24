from __future__ import annotations

from collections import defaultdict

from oe_ce.apparel_rungs import ARMOR
from oe_ce.emit_apparel import member_ops
from oe_ce.emit_common import (
    ensure_node,
    format_num,
    named_xpath,
    set_stat,
    set_xpath_value,
    thing_xpath,
    wrap_may_require,
)
from oe_ce.scan_shields import CoreShield
from oe_ce.shield_models import HandheldSet, ShieldCatalog, ShieldMember, WornSet
from oe_ce.shield_rungs import (
    HANDHELD_COVERAGE,
    HANDHELD_PENALTIES,
    energy_stats,
    handheld_stats,
    innate_energy,
)

_ABSTRACT_SHIELDS = ("OEShieldBase", "OEShieldBaseNQ")
_MU_TAG = "MU.MechUpgradeDef"
_UPGRADE_COMP = "MU.UpgradeCompProperties_ShieldUpgrade"


def _patch(ops: list[str]) -> str:
    inner = "\n".join(ops)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>\n'


def _energy_ops(def_name: str, rung: str, role: str) -> list[str]:
    stats = energy_stats(rung, role)
    return [
        ensure_node(def_name, "statBases"),
        set_stat(def_name, "statBases", "EnergyShieldEnergyMax", stats.energy_max),
        set_stat(def_name, "statBases", "EnergyShieldRechargeRate", stats.recharge),
    ]


def _worn_ops(worn: WornSet, member: ShieldMember) -> list[str]:
    rung = worn.member_rung(member)
    ops = _energy_ops(member.def_name, rung, worn.role)
    if worn.plate == "emit":
        ops.extend(member_ops(ARMOR, member.def_name, rung, False))
    return ops


def _maybe_wrap(ops: list[str], may_require: str | None) -> list[str]:
    if not ops:
        return []
    if may_require:
        return [wrap_may_require(ops, may_require)]
    return ops


def _replace_node(xpath: str, xml: str) -> str:
    return f"""  <Operation Class="PatchOperationReplace">
    <xpath>{xpath}</xpath>
    <value>
{xml}
    </value>
  </Operation>"""


def _remove_if_present(xpath: str) -> str:
    return f"""  <Operation Class="PatchOperationConditional">
    <xpath>{xpath}</xpath>
    <match Class="PatchOperationRemove">
      <xpath>{xpath}</xpath>
    </match>
  </Operation>"""


def _abstract_handheld_ops() -> list[str]:
    ops: list[str] = []
    for name in _ABSTRACT_SHIELDS:
        base = named_xpath(name)
        ops.append(
            _replace_node(
                f"{base}/thingClass",
                "      <thingClass>CombatExtended.Apparel_Shield</thingClass>",
            )
        )
        ops.append(
            _replace_node(
                f"{base}/apparel/bodyPartGroups",
                "      <bodyPartGroups>\n        <li>LeftShoulder</li>\n      </bodyPartGroups>",
            )
        )
        ops.append(
            _replace_node(
                f"{base}/apparel/layers",
                "      <layers>\n        <li>Shield</li>\n      </layers>",
            )
        )
    return ops


def _penalties_xml(size: str) -> str:
    lines = ["      <equippedStatOffsets>"]
    for stat, value in HANDHELD_PENALTIES[size].items():
        lines.append(f"        <{stat}>{format_num(value)}</{stat}>")
    lines.append("      </equippedStatOffsets>")
    return "\n".join(lines)


def _coverage_xml(size: str) -> str:
    cover, crouch = HANDHELD_COVERAGE[size]
    cover_lis = "\n".join(f"            <li>{part}</li>" for part in cover)
    lines = [
        '      <li Class="CombatExtended.ShieldDefExtension">',
        "        <shieldCoverage>",
        cover_lis,
        "        </shieldCoverage>",
    ]
    if crouch:
        crouch_lis = "\n".join(f"            <li>{part}</li>" for part in crouch)
        lines += ["        <crouchCoverage>", crouch_lis, "        </crouchCoverage>"]
    lines.append("      </li>")
    return "\n".join(lines)


def _render_xml(tex_path: str, size: str) -> str:
    extra_east = ""
    extra_west = ""
    south = "            <offset>(0.25, 0, -0.15)</offset>"
    if size == "big":
        extra_east = "\n              <rotationOffset>30</rotationOffset>"
        extra_west = """
            <dataWest>
              <rotationOffset>-30</rotationOffset>
            </dataWest>"""
        south = "            <offset>(0.15, 0, -0.1)</offset>"
    return f"""        <renderNodeProperties>
          <li>
            <nodeClass>CombatExtended.PawnRenderNode_Apparel</nodeClass>
            <workerClass>CombatExtended.PawnRenderNodeWorker_Drafted</workerClass>
            <texPath>{tex_path}</texPath>
            <shaderTypeDef>CutoutComplex</shaderTypeDef>
            <parentTagDef>ApparelBody</parentTagDef>
            <drawData>
              <scale>0.8</scale>
              <defaultData>
                <layer>85</layer>
              </defaultData>
              <dataEast>
                <layer>-5</layer>
                <offset>(0, 0, -0.1)</offset>{extra_east}
              </dataEast>{extra_west}
              <dataNorth>
                <layer>-5</layer>
                <offset>(0.15, 0, -0.1)</offset>
              </dataNorth>
              <dataSouth>
{south}
              </dataSouth>
            </drawData>
          </li>
        </renderNodeProperties>"""


def _replace_or_add(def_name: str, node: str, xml: str) -> str:
    base = thing_xpath(def_name)
    return f"""  <Operation Class="PatchOperationConditional">
    <xpath>{base}/{node}</xpath>
    <match Class="PatchOperationReplace">
      <xpath>{base}/{node}</xpath>
      <value>
{xml}
      </value>
    </match>
    <nomatch Class="PatchOperationAdd">
      <xpath>{base}</xpath>
      <value>
{xml}
      </value>
    </nomatch>
  </Operation>"""


def _handheld_member_ops(hand: HandheldSet, member: ShieldMember, scanned: dict[str, CoreShield]) -> list[str]:
    name = member.def_name
    base = thing_xpath(name)
    rung = hand.member_rung(member)
    stats = handheld_stats(
        rung,
        hand.size,
        mass=member.mass,
        bulk=member.bulk,
        worn_bulk=member.worn_bulk,
    )
    info = scanned.get(name)
    tex_path = info.tex_path if info is not None and info.tex_path else name
    ops = [
        _remove_if_present(f'{base}/comps/li[@Class="VEF.Apparels.CompProperties_Shield"]'),
        _remove_if_present(f"{base}/tools"),
        _replace_or_add(name, "equippedStatOffsets", _penalties_xml(hand.size)),
        ensure_node(name, "statBases"),
        set_stat(name, "statBases", "ArmorRating_Sharp", stats.sharp),
        set_stat(name, "statBases", "ArmorRating_Blunt", stats.blunt),
        set_stat(name, "statBases", "ArmorRating_Heat", stats.heat),
        set_stat(name, "statBases", "Mass", stats.mass),
        set_stat(name, "statBases", "Bulk", stats.bulk),
        set_stat(name, "statBases", "WornBulk", stats.worn_bulk),
        f"""  <Operation Class="PatchOperationAddModExtension">
    <xpath>{base}</xpath>
    <value>
{_coverage_xml(hand.size)}
    </value>
  </Operation>""",
        ensure_node(name, "apparel"),
        f"""  <Operation Class="PatchOperationAdd">
    <xpath>{base}/apparel</xpath>
    <value>
{_render_xml(tex_path, hand.size)}
    </value>
  </Operation>""",
    ]
    return ops


def emit_worn_handheld_xml(cat: ShieldCatalog, scanned: dict[str, CoreShield]) -> str:
    grouped: dict[str | None, list[str]] = defaultdict(list)
    worn_rows = sorted(
        ((s, m) for s in cat.worn for m in s.members),
        key=lambda row: row[1].def_name,
    )
    for worn, member in worn_rows:
        grouped[worn.may_require].extend(_worn_ops(worn, member))

    vef_ops = _abstract_handheld_ops()
    oec_ops: list[str] = []
    hand_rows = sorted(
        ((s, m) for s in cat.handheld for m in s.members),
        key=lambda row: row[1].def_name,
    )
    for hand, member in hand_rows:
        ops = _handheld_member_ops(hand, member, scanned)
        if hand.may_require and "," in (hand.may_require or ""):
            oec_ops.extend(ops)
        else:
            vef_ops.extend(ops)

    blocks: list[str] = []
    for may_require in sorted(grouped, key=lambda key: key or ""):
        blocks.extend(_maybe_wrap(grouped[may_require], may_require))
    if cat.handheld:
        vef_pkg = next(
            (s.may_require for s in cat.handheld if s.may_require and "," not in s.may_require),
            "OskarPotocki.VanillaFactionsExpanded.Core",
        )
        blocks.append(wrap_may_require(vef_ops, vef_pkg or "OskarPotocki.VanillaFactionsExpanded.Core"))
    if oec_ops:
        oec_pkg = next(
            (s.may_require for s in cat.handheld if s.may_require and "," in s.may_require),
            "OskarPotocki.VanillaFactionsExpanded.Core,Ludeon.RimWorld.Royalty",
        )
        blocks.append(wrap_may_require(oec_ops, oec_pkg))
    return _patch(blocks)


def emit_innate_xml(cat: ShieldCatalog) -> str:
    grouped: dict[str, list[str]] = defaultdict(list)
    rows = sorted(
        ((s, m) for s in cat.innate for m in s.members),
        key=lambda row: row[1].def_name,
    )
    for innate, member in rows:
        stats = innate_energy(innate.analogue)
        pkg = innate.may_require or "Ludeon.RimWorld.Biotech"
        grouped[pkg].extend(
            [
                ensure_node(member.def_name, "statBases"),
                set_stat(member.def_name, "statBases", "EnergyShieldEnergyMax", stats.energy_max),
                set_stat(
                    member.def_name, "statBases", "EnergyShieldRechargeRate", stats.recharge
                ),
            ]
        )
    blocks = [wrap_may_require(ops, pkg) for pkg, ops in grouped.items() if ops]
    return _patch(blocks)


def emit_upgrade_xml(cat: ShieldCatalog) -> str:
    blocks: list[str] = []
    for upgrade in cat.upgrades:
        ops: list[str] = []
        for member in upgrade.members:
            ops.append(ensure_node(member.def_name, "statFactors", _MU_TAG))
            ops.append(
                set_stat(
                    member.def_name,
                    "statFactors",
                    "EnergyShieldEnergyMax",
                    upgrade.factor,
                    _MU_TAG,
                )
            )
            parent = (
                f'{thing_xpath(member.def_name, _MU_TAG)}'
                f'/comps/li[@Class="{_UPGRADE_COMP}"]'
            )
            ops.append(set_xpath_value(parent, "factor", upgrade.factor))
        if ops:
            blocks.extend(_maybe_wrap(ops, upgrade.may_require))
    return _patch(blocks)
