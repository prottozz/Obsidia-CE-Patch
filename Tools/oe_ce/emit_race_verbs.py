"""CE verbs + projectiles for innate ranged attacks of catalogued races (slice 11).

Today: the four Bruuls' ink. Each Obsidia race projectile gets a dedicated CE copy
(`Bullet_OE_<name>_CE`); the Obsidia projectile stays untouched. Non-explosive
spit is a blunt glob with Obsidia's element as CE secondary damage; an explosive
projectile uses the slice 10 explosive rules.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET

from oe_ce.emit_common import thing_xpath, wrap_optional_def
from oe_ce.explosive import Blast, explosive_round
from oe_ce.scan_obsidia import ThingDefIndex, walk_parents

INK_BLUNT_AP = 6  # armorPenetrationBlunt of the glob's impact
EMP_SHIELD_BREAK = 0.15
_SKIP_VERB_TAGS = frozenset({"verbClass", "defaultProjectile"})


@dataclass(frozen=True)
class RaceProjectile:
    def_name: str
    label: str | None
    graphic: ET.Element | None
    damage_def: str
    amount: float
    speed: float
    radius: float
    thing_class: str | None

    @property
    def ce_def(self) -> str:
        stem = self.def_name[len("Bullet_"):] if self.def_name.startswith("Bullet_") else self.def_name
        return f"Bullet_OE_{stem}_CE"


@dataclass
class RaceVerbs:
    race: str
    package: str | None
    verbs: list[tuple[ET.Element, RaceProjectile]] = field(default_factory=list)


def _inherited(index: ThingDefIndex, el: ET.Element, path: str) -> ET.Element | None:
    for node in walk_parents(index, el):
        found = node.find(path)
        if found is not None:
            return found
    return None


def _text(index: ThingDefIndex, el: ET.Element, path: str) -> str | None:
    found = _inherited(index, el, path)
    if found is None or not (found.text or "").strip():
        return None
    return found.text.strip()


def _num(text: str | None, default: float) -> float:
    try:
        return float(text) if text is not None else default
    except ValueError:
        return default


def scan_race_verbs(
    index: ThingDefIndex, races: dict[str, str | None]
) -> tuple[list[RaceVerbs], list[str]]:
    """``races`` maps catalogued race defName -> mayRequire package."""
    out: list[RaceVerbs] = []
    errors: list[str] = []
    for race, package in sorted(races.items()):
        el = index.by_def.get(race)
        if el is None:
            continue
        verbs = _inherited(index, el, "verbs")
        if verbs is None:
            continue
        if el.find("verbs") is None and any(
            (li.findtext("defaultProjectile") or "").strip() for li in verbs.findall("li")
        ):
            errors.append(f"{race}: ranged verbs inherited from a parent; patch the parent instead")
            continue
        entry = RaceVerbs(race, package)
        for li in verbs.findall("li"):
            proj_name = (li.findtext("defaultProjectile") or "").strip()
            if not proj_name:
                continue
            proj = index.by_def.get(proj_name)
            if proj is None:
                errors.append(f"{race}: ranged verb projectile {proj_name} not found")
                continue
            entry.verbs.append(
                (
                    li,
                    RaceProjectile(
                        def_name=proj_name,
                        label=_text(index, proj, "label"),
                        graphic=_inherited(index, proj, "graphicData"),
                        damage_def=_text(index, proj, "projectile/damageDef") or "Bullet",
                        amount=_num(_text(index, proj, "projectile/damageAmountBase"), 10),
                        speed=_num(_text(index, proj, "projectile/speed"), 40),
                        radius=_num(_text(index, proj, "projectile/explosionRadius"), 0),
                        thing_class=_text(index, proj, "thingClass"),
                    ),
                )
            )
        if entry.verbs:
            out.append(entry)
    return out, errors


def _clean(el: ET.Element, indent: str) -> str:
    c = copy.deepcopy(el)
    c.tail = None
    ET.indent(c, space="  ")
    text = ET.tostring(c, encoding="unicode").strip()
    return "\n".join(indent + line for line in text.split("\n"))


def _num_xml(value: float) -> str:
    return str(int(value)) if value == int(value) else format(value, "g")


def race_projectile_def(proj: RaceProjectile) -> str:
    graphic = _clean(proj.graphic, "  ") if proj.graphic is not None else ""
    label = f"\n  <label>{proj.label}</label>" if proj.label else ""
    if proj.radius > 0:
        rnd = explosive_round(
            Blast(proj.damage_def, proj.amount, proj.radius, proj.thing_class), "launcher", "standard"
        )
        return f"""<ThingDef ParentName="BaseExplosiveBullet">
  <defName>{proj.ce_def}</defName>{label}
  <thingClass>CombatExtended.ProjectileCE_Explosive</thingClass>
{graphic}
  <projectile Class="CombatExtended.ProjectilePropertiesCE">
    <damageDef>{rnd.damage_def}</damageDef>
    <damageAmountBase>{rnd.damage}</damageAmountBase>
    <explosionRadius>{rnd.radius:g}</explosionRadius>
    <speed>{_num_xml(proj.speed)}</speed>
  </projectile>
</ThingDef>"""
    extras = ""
    if proj.damage_def == "EMP":
        extras += f"\n    <empShieldBreakChance>{EMP_SHIELD_BREAK:g}</empShieldBreakChance>"
    if proj.damage_def == "Flame":
        extras += "\n    <ai_IsIncendiary>true</ai_IsIncendiary>"
    return f"""<ThingDef ParentName="BaseBulletCE">
  <defName>{proj.ce_def}</defName>{label}
{graphic}
  <projectile Class="CombatExtended.ProjectilePropertiesCE">
    <damageDef>Blunt</damageDef>
    <damageAmountBase>{_num_xml(proj.amount)}</damageAmountBase>
    <armorPenetrationSharp>0</armorPenetrationSharp>
    <armorPenetrationBlunt>{INK_BLUNT_AP}</armorPenetrationBlunt>
    <speed>{_num_xml(proj.speed)}</speed>
    <secondaryDamage>
      <li>
        <def>{proj.damage_def}</def>
        <amount>{_num_xml(proj.amount)}</amount>
      </li>
    </secondaryDamage>{extras}
  </projectile>
</ThingDef>"""


def race_projectile_defs(entries: list[RaceVerbs]) -> list[str]:
    seen: dict[str, RaceProjectile] = {}
    for entry in entries:
        for _li, proj in entry.verbs:
            seen.setdefault(proj.ce_def, proj)
    return [race_projectile_def(p) for _name, p in sorted(seen.items())]


def _verb_li(li: ET.Element, proj: RaceProjectile) -> str:
    rows = ["          <verbClass>CombatExtended.Verb_ShootCE</verbClass>"]
    for child in li:
        if child.tag in _SKIP_VERB_TAGS:
            continue
        rows.append(_clean(child, "          "))
    rows.append(f"          <defaultProjectile>{proj.ce_def}</defaultProjectile>")
    body = "\n".join(rows)
    return f"""        <li Class="CombatExtended.VerbPropertiesCE">
{body}
        </li>"""


def emit_race_verb_xml(entries: list[RaceVerbs]) -> str:
    blocks: list[str] = []
    for entry in entries:
        lis = "\n".join(_verb_li(li, proj) for li, proj in entry.verbs)
        op = f"""  <Operation Class="PatchOperationReplace">
    <xpath>{thing_xpath(entry.race)}/verbs</xpath>
    <value>
      <verbs>
{lis}
      </verbs>
    </value>
  </Operation>"""
        blocks.append(wrap_optional_def([op], entry.package or "", entry.race))
    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>\n'
