from __future__ import annotations

from oe_ce.models import Family

EMP_SIDE_AMOUNT = 6
EMP_DEDICATED_AMOUNT = 18

_AMMO_CLASS = {
    "standard": "FMJ",
    "ap": "ArmorPiercing",
    "hp": "HollowPoint",
    "emp": "Ionized",
}

_PROJECTILE = {
    "standard": (13, 18, 26),
    "ap": (10, 32, 26),
    "hp": (16, 10, 26),
    "emp": (8, 12, 26),
}

_TEX_PATH = "Things/Ammo/Charged/MediumRegular"


def _category_def_name(fam: Family) -> str:
    return f"AmmoOE_{fam.id}_{fam.class_name}"


def _category_label(fam: Family) -> str:
    return f"OE {fam.id} {fam.class_name}"


def _emit_thing_category(fam: Family) -> str:
    return f"""<ThingCategoryDef>
  <defName>{_category_def_name(fam)}</defName>
  <label>{_category_label(fam)}</label>
  <parent>AmmoAdvanced</parent>
</ThingCategoryDef>"""


def _emit_ammo_set(fam: Family) -> str:
    cartridges = fam.resolved_cartridges()
    lines = ["  <ammoTypes>"]
    for cart in cartridges:
        ammo = fam.ammo_def(cart)
        bullet = fam.bullet_def(cart)
        lines.append(f"    <{ammo}>{bullet}</{ammo}>")
    lines.append("  </ammoTypes>")
    inner = "\n".join(lines)
    return f"""<CombatExtended.AmmoSetDef>
  <defName>{fam.ammo_set_def()}</defName>
{inner}
</CombatExtended.AmmoSetDef>"""


def _emit_ammo_def(fam: Family, cartridge: str) -> str:
    return f"""<ThingDef Class="CombatExtended.AmmoDef" ParentName="SpacerSmallAmmoBase">
  <defName>{fam.ammo_def(cartridge)}</defName>
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


def _emp_secondary_xml(amount: int, shield_chance: str) -> str:
    return f"""    <secondaryDamage>
      <li>
        <def>EMP</def>
        <amount>{amount}</amount>
      </li>
    </secondaryDamage>
    <empShieldBreakChance>{shield_chance}</empShieldBreakChance>"""


def _emit_bullet(fam: Family, cartridge: str) -> str:
    damage, sharp, blunt = _PROJECTILE[cartridge]
    emp_extra = ""
    if fam.class_name == "emp":
        emp_extra = "\n" + _emp_secondary_xml(
            EMP_DEDICATED_AMOUNT, "0.45"
        )
    elif cartridge == "emp":
        emp_extra = "\n" + _emp_secondary_xml(EMP_SIDE_AMOUNT, "0.15")

    return f"""<ThingDef ParentName="BaseBulletCE">
  <defName>{fam.bullet_def(cartridge)}</defName>
  <projectile Class="CombatExtended.ProjectilePropertiesCE">
    <damageDef>Bullet</damageDef>
    <damageAmountBase>{damage}</damageAmountBase>
    <armorPenetrationSharp>{sharp}</armorPenetrationSharp>
    <armorPenetrationBlunt>{blunt}</armorPenetrationBlunt>{emp_extra}
  </projectile>
</ThingDef>"""


def _emit_family(fam: Family) -> list[str]:
    blocks: list[str] = [_emit_thing_category(fam), _emit_ammo_set(fam)]
    for cart in fam.resolved_cartridges():
        blocks.append(_emit_ammo_def(fam, cart))
        blocks.append(_emit_bullet(fam, cart))
    return blocks


def emit_ammo_xml(families: list[Family]) -> str:
    sorted_families = sorted(families, key=lambda f: (f.class_name, f.id))
    body: list[str] = []
    for fam in sorted_families:
        body.extend(_emit_family(fam))
    inner = "\n\n".join(body)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n{inner}\n</Defs>'
