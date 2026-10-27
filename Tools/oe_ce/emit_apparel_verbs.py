"""CE deploy verbs for DLC apparel: turret packs, disruptor flares, gas darts.

Every verb becomes ``Verb_LaunchProjectileStaticCE`` (the reloadable-aware CE
static launcher CE uses for the vanilla flare pack and that our grenade belts
already use). CE's ``Verb_ShootCEOneUse*`` is avoided on purpose: its
SelfConsume path can swap the wearer's weapon after a deploy.
"""

from __future__ import annotations

import copy
import xml.etree.ElementTree as ET

from oe_ce.emit_common import thing_xpath, wrap_optional_def
from oe_ce.scan_apparel_verbs import FLARE, GAS, TURRET, ApparelVerbScan, DeployProjectile

_CE_VERB = "CombatExtended.Verb_LaunchProjectileStaticCE"
# forcedMissRadius: vanilla ConfigErrors demands it only for vanilla-explosive
# projectiles; ProjectileCE_Explosive does not count, so keeping Obsidia's 0.1
# on the deadlife dart is a load error. CE handles spread itself (same as belts).
_SKIP_TAGS = frozenset({"verbClass", "forcedMissRadius"})
# CE extras every static deploy verb gets (same as the grenade belts / CE flare pack).
_CE_EXTRAS = (
    ("ignorePartialLoSBlocker", "true"),
    ("drawHighlightWithLineOfSight", "true"),
)
_THING_CLASS = {
    TURRET: "CombatExtended.ProjectileCE_SpawnsThing",
    FLARE: "CombatExtended.ProjectileCE_SpawnsThing",
    GAS: "CombatExtended.ProjectileCE_Explosive",
}
# Field order and fixed values follow CE 1.7-Test's own patches of
# Grenade_TurretPack / Grenade_DisruptorFlare / Grenade_Deadlife.
_KEEP = {
    TURRET: ("spawnsThingDef", "tryAdjacentFreeSpaces"),
    FLARE: ("spinRate", "landedEffecter", "spawnsThingDef"),
    GAS: ("explosionRadius", "damageDef", "soundExplode", "postExplosionSpawnThingDef"),
}
_FIXED = {
    TURRET: (("dropsCasings", "false"), ("dangerFactor", "0"), ("airborneSuppressionFactor", "0"), ("speed", "12")),
    FLARE: (("dropsCasings", "false"), ("dangerFactor", "0"), ("airborneSuppressionFactor", "0"), ("speed", "12")),
    GAS: (("damageAmountBase", "0"), ("speed", "12")),
}


def _indent(xml: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else line for line in xml.split("\n"))


def _verb_li(li: ET.Element) -> str:
    rows = [f"<verbClass>{_CE_VERB}</verbClass>"]
    present = set()
    for child in li:
        if child.tag in _SKIP_TAGS:
            continue
        present.add(child.tag)
        clean = copy.deepcopy(child)
        clean.tail = None
        ET.indent(clean, space="  ")
        text = ET.tostring(clean, encoding="unicode").strip()
        rows.append(text)
    for tag, value in _CE_EXTRAS:
        if tag not in present:
            rows.append(f"<{tag}>{value}</{tag}>")
    body = "\n".join(_indent(row, 2) for row in rows)
    return f'<li Class="CombatExtended.VerbPropertiesCE">\n{body}\n</li>'


def _verbs_op(def_name: str, verbs: tuple[ET.Element, ...]) -> str:
    lis = "\n".join(_indent(_verb_li(li), 8) for li in verbs)
    return f"""  <Operation Class="PatchOperationReplace">
    <xpath>{thing_xpath(def_name)}/verbs</xpath>
    <value>
      <verbs>
{lis}
      </verbs>
    </value>
  </Operation>"""


def _projectile_ops(proj: DeployProjectile) -> list[str]:
    base = thing_xpath(proj.def_name)
    rows = [f"<{tag}>{value}</{tag}>" for tag, value in _FIXED[proj.kind]]
    for tag in _KEEP[proj.kind]:
        value = proj.field(tag)
        if value is not None:
            rows.append(f"<{tag}>{value}</{tag}>")
    body = "\n".join(f"          {row}" for row in rows)
    return [
        f"""  <Operation Class="PatchOperationReplace">
    <xpath>{base}/thingClass</xpath>
    <value>
      <thingClass>{_THING_CLASS[proj.kind]}</thingClass>
    </value>
  </Operation>""",
        f"""  <Operation Class="PatchOperationReplace">
    <xpath>{base}/projectile</xpath>
    <value>
      <projectile Class="CombatExtended.ProjectilePropertiesCE">
{body}
      </projectile>
    </value>
  </Operation>""",
    ]


def emit_apparel_verb_xml(scan: ApparelVerbScan) -> str:
    blocks: list[str] = []
    for name, apparel in sorted(scan.apparel.items()):
        blocks.append(wrap_optional_def([_verbs_op(name, apparel.verbs)], apparel.package, name))
    for name, proj in sorted(scan.projectiles.items()):
        blocks.append(wrap_optional_def(_projectile_ops(proj), proj.package, name))
    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>\n'
