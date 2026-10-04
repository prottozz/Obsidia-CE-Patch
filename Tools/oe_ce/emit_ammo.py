from __future__ import annotations

from pathlib import Path

from oe_ce.models import Family, Member, unique_ammo_families
from oe_ce.scan_obsidia import (
    ProjectileGraphic,
    ThingDefIndex,
    index_weapon_thingdefs,
    weapon_projectile_graphic,
)

EMP_SIDE_AMOUNT = 6
EMP_DEDICATED_AMOUNT = 18

_AMMO_CLASS = {
    "standard": "FullMetalJacket",
    "ap": "ArmorPiercing",
    "hp": "HollowPoint",
    "emp": "Ionized",
    "fire": "OE_Fire",
    "acid": "OE_Acid",
    "cryo": "OE_Cryo",
    "bio": "OE_Bio",
    "energy": "Charged",
}

_CUSTOM_AMMO_CATEGORIES = (
    ("OE_Fire", "fire", "Fire"),
    ("OE_Acid", "acid", "Acid"),
    ("OE_Cryo", "cryo", "Cryo"),
    ("OE_Bio", "bio", "Bio"),
)

_PROJECTILE = {
    "standard": (13, 18, 26),
    "ap": (10, 32, 26),
    "hp": (16, 10, 26),
    "emp": (8, 12, 26),
    "fire": (13, 18, 26),
    "acid": (12, 40, 26),
    "cryo": (13, 18, 26),
    "bio": (13, 18, 26),
    "energy": (13, 18, 26),
}

_TEX_PATH = "Things/Ammo/Charged/MediumRegular"
_FALLBACK_BULLET_TEX = "Things/Projectile/Charged/ChargeShot"
_FALLBACK_BULLET_CLASS = "Graphic_Single"


def _category_def_name(fam: Family) -> str:
    return f"AmmoOE_{fam.caliber()}_{fam.class_name}"


def _category_label(fam: Family) -> str:
    return f"OE {fam.display_label()} {fam.class_name}"


def _ammo_label(fam: Family, cartridge: str) -> str:
    if cartridge == fam.class_name:
        return f"{fam.display_label()} {fam.class_name}"
    return f"{fam.display_label()} {fam.class_name} {cartridge}"


def _ammo_set_label(fam: Family, member: Member) -> str:
    return f"{member.def_name} {fam.display_label()} {fam.class_name}"


def _emit_thing_category(fam: Family) -> str:
    return f"""<ThingCategoryDef>
  <defName>{_category_def_name(fam)}</defName>
  <label>{_category_label(fam)}</label>
  <parent>AmmoAdvanced</parent>
</ThingCategoryDef>"""


def _emit_ammo_set(fam: Family, member: Member) -> str:
    cartridges = fam.resolved_cartridges()
    lines = ["  <ammoTypes>"]
    for cart in cartridges:
        ammo = fam.ammo_def(cart)
        bullet = fam.member_bullet_def(member, cart)
        lines.append(f"    <{ammo}>{bullet}</{ammo}>")
    lines.append("  </ammoTypes>")
    inner = "\n".join(lines)
    return f"""<CombatExtended.AmmoSetDef>
  <defName>{fam.member_ammo_set_def(member)}</defName>
  <label>{_ammo_set_label(fam, member)}</label>
{inner}
</CombatExtended.AmmoSetDef>"""


def _emit_ammo_def(fam: Family, cartridge: str) -> str:
    category = _category_def_name(fam)
    return f"""<ThingDef Class="CombatExtended.AmmoDef" ParentName="SpacerSmallAmmoBase">
  <defName>{fam.ammo_def(cartridge)}</defName>
  <label>{_ammo_label(fam, cartridge)}</label>
  <statBases>
    <Mass>0.01</Mass>
    <Bulk>0.01</Bulk>
  </statBases>
  <thingCategories>
    <li>{category}</li>
  </thingCategories>
  <graphicData>
    <texPath>{_TEX_PATH}</texPath>
    <graphicClass>Graphic_StackCount</graphicClass>
  </graphicData>
  <ammoClass>{_AMMO_CLASS[cartridge]}</ammoClass>
  <tradeTags>
    <li>CE_AutoEnableTrade</li>
    <li>OEGear</li>
  </tradeTags>
</ThingDef>"""


def _emit_ammo_categories() -> list[str]:
    blocks: list[str] = []
    for def_name, label, short in _CUSTOM_AMMO_CATEGORIES:
        blocks.append(
            f"""<CombatExtended.AmmoCategoryDef>
  <defName>{def_name}</defName>
  <label>{label}</label>
  <labelShort>{short}</labelShort>
</CombatExtended.AmmoCategoryDef>"""
        )
    return blocks


def _secondary_xml(hits: list[tuple[str, int]]) -> str:
    lines = ["    <secondaryDamage>"]
    for def_name, amount in hits:
        lines.append("      <li>")
        lines.append(f"        <def>{def_name}</def>")
        lines.append(f"        <amount>{amount}</amount>")
        lines.append("      </li>")
    lines.append("    </secondaryDamage>")
    return "\n".join(lines)


def _projectile_extras(fam: Family, cartridge: str) -> str:
    extras: list[str] = []
    if cartridge == "fire":
        extras.append(_secondary_xml([("Flame", 8)]))
        extras.append("    <ai_IsIncendiary>true</ai_IsIncendiary>")
    elif cartridge == "acid":
        extras.append(_secondary_xml([("OTCAcid", 8)]))
    elif cartridge == "cryo":
        extras.append(_secondary_xml([("OTCCryo", 8)]))
    elif cartridge == "bio":
        extras.append(_secondary_xml([("OTCAcid", 6), ("OTCCryo", 6)]))
    elif cartridge == "emp":
        amount = EMP_DEDICATED_AMOUNT if fam.class_name == "emp" else EMP_SIDE_AMOUNT
        chance = "0.45" if fam.class_name == "emp" else "0.15"
        extras.append(_secondary_xml([("EMP", amount)]))
        extras.append(f"    <empShieldBreakChance>{chance}</empShieldBreakChance>")
    if not extras:
        return ""
    return "\n" + "\n".join(extras)


def _graphic_xml(graphic: ProjectileGraphic | None) -> str:
    tex = graphic.tex_path if graphic is not None else _FALLBACK_BULLET_TEX
    cls = graphic.graphic_class if graphic is not None else _FALLBACK_BULLET_CLASS
    lines = [
        "  <graphicData>",
        f"    <texPath>{tex}</texPath>",
        f"    <graphicClass>{cls}</graphicClass>",
    ]
    if graphic is not None and graphic.draw_size:
        lines.append(f"    <drawSize>{graphic.draw_size}</drawSize>")
    lines.append("  </graphicData>")
    return "\n".join(lines)


def _emit_bullet(
    fam: Family,
    member: Member,
    cartridge: str,
    graphic: ProjectileGraphic | None,
) -> str:
    damage, sharp, blunt = _PROJECTILE[cartridge]
    extra = _projectile_extras(fam, cartridge)
    return f"""<ThingDef ParentName="BaseBulletCE">
  <defName>{fam.member_bullet_def(member, cartridge)}</defName>
{_graphic_xml(graphic)}
  <projectile Class="CombatExtended.ProjectilePropertiesCE">
    <damageDef>Bullet</damageDef>
    <damageAmountBase>{damage}</damageAmountBase>
    <armorPenetrationSharp>{sharp}</armorPenetrationSharp>
    <armorPenetrationBlunt>{blunt}</armorPenetrationBlunt>
    <speed>151</speed>{extra}
  </projectile>
</ThingDef>"""


def emit_ammo_xml(families: list[Family], core: Path | None = None) -> str:
    index: ThingDefIndex | None = index_weapon_thingdefs(core) if core is not None else None
    body: list[str] = _emit_ammo_categories()
    for fam in unique_ammo_families(families):
        body.append(_emit_thing_category(fam))
        for cart in fam.resolved_cartridges():
            body.append(_emit_ammo_def(fam, cart))
    for fam in families:
        for member in sorted(fam.members, key=lambda m: m.def_name):
            graphic = (
                weapon_projectile_graphic(core, member.def_name, index=index)
                if core is not None
                else None
            )
            body.append(_emit_ammo_set(fam, member))
            for cart in fam.resolved_cartridges():
                body.append(_emit_bullet(fam, member, cart, graphic))
    inner = "\n\n".join(body)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n{inner}\n</Defs>'
