from __future__ import annotations

from oe_ce.apparel_rungs import ARMOR
from oe_ce.emit_apparel import member_ops
from oe_ce.emit_common import (
    ensure_node,
    format_num,
    named_xpath,
    set_stat,
    set_xpath_value,
    thing_xpath,
    wrap_optional_def,
    wrap_optional_xpath,
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


def _replace_or_add_at(base: str, node: str, xml: str) -> str:
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


def _abstract_ops(name: str) -> list[str]:
    base = named_xpath(name)
    return [
        _replace_or_add_at(
            base,
            "thingClass",
            "      <thingClass>CombatExtended.Apparel_Shield</thingClass>",
        ),
        _replace_or_add_at(
            base,
            "apparel/bodyPartGroups",
            "      <bodyPartGroups>\n        <li>LeftShoulder</li>\n      </bodyPartGroups>",
        ),
        _replace_or_add_at(
            base,
            "apparel/layers",
            "      <layers>\n        <li>Shield</li>\n      </layers>",
        ),
    ]


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
    return _replace_or_add_at(thing_xpath(def_name), node, xml)


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
    core_worn: list[str] = []
    optional_worn: list[str] = []
    worn_rows = sorted(
        ((s, m) for s in cat.worn for m in s.members),
        key=lambda row: row[1].def_name,
    )
    for worn, member in worn_rows:
        ops = _worn_ops(worn, member)
        if worn.may_require:
            optional_worn.append(
                wrap_optional_def(ops, worn.may_require, member.def_name)
            )
        else:
            core_worn.extend(ops)

    vef_pkg = next(
        (s.may_require for s in cat.handheld if s.may_require and "," not in s.may_require),
        "OskarPotocki.VanillaFactionsExpanded.Core",
    ) or "OskarPotocki.VanillaFactionsExpanded.Core"

    blocks: list[str] = list(core_worn)
    blocks.extend(optional_worn)
    if cat.handheld:
        for name in _ABSTRACT_SHIELDS:
            blocks.append(
                wrap_optional_xpath(_abstract_ops(name), vef_pkg, named_xpath(name))
            )
        hand_rows = sorted(
            ((s, m) for s in cat.handheld for m in s.members),
            key=lambda row: row[1].def_name,
        )
        for hand, member in hand_rows:
            pkg = hand.may_require or vef_pkg
            blocks.append(
                wrap_optional_def(_handheld_member_ops(hand, member, scanned), pkg, member.def_name)
            )
    return _patch(blocks)


def emit_innate_xml(cat: ShieldCatalog) -> str:
    rows = sorted(
        ((s, m) for s in cat.innate for m in s.members),
        key=lambda row: row[1].def_name,
    )
    blocks: list[str] = []
    for innate, member in rows:
        stats = innate_energy(innate.analogue)
        pkg = innate.may_require or "Ludeon.RimWorld.Biotech"
        ops = [
            ensure_node(member.def_name, "statBases"),
            set_stat(member.def_name, "statBases", "EnergyShieldEnergyMax", stats.energy_max),
            set_stat(
                member.def_name, "statBases", "EnergyShieldRechargeRate", stats.recharge
            ),
        ]
        blocks.append(wrap_optional_def(ops, pkg, member.def_name))
    return _patch(blocks)


def emit_upgrade_xml(cat: ShieldCatalog) -> str:
    blocks: list[str] = []
    for upgrade in cat.upgrades:
        for member in upgrade.members:
            parent = (
                f'{thing_xpath(member.def_name, _MU_TAG)}'
                f'/comps/li[@Class="{_UPGRADE_COMP}"]'
            )
            ops = [
                ensure_node(member.def_name, "statFactors", _MU_TAG),
                set_stat(
                    member.def_name,
                    "statFactors",
                    "EnergyShieldEnergyMax",
                    upgrade.factor,
                    _MU_TAG,
                ),
                set_xpath_value(parent, "factor", upgrade.factor),
            ]
            if upgrade.may_require:
                blocks.append(
                    wrap_optional_def(
                        ops, upgrade.may_require, member.def_name, _MU_TAG
                    )
                )
            else:
                blocks.extend(ops)
    return _patch(blocks)
