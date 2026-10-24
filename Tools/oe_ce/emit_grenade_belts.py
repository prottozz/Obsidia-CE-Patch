from __future__ import annotations

from oe_ce.emit_common import named_xpath, thing_xpath, wrap_optional_def, wrap_optional_xpath

GRENADE_BELTS = (
    ("OTC_GrenadeBelt_Acid", "Grenade_GrenadeBelt_OTC_Acid", "throw acid grenade", 15.9),
    ("OTC_GrenadeBelt_Cryo", "Grenade_GrenadeBelt_OTC_Cryo", "throw cryo grenade", 15.9),
    ("OTC_GrenadeBelt_Fire", "Grenade_GrenadeBelt_OTC_Fire", "throw fire grenade", 15.9),
    ("OTC_GrenadeBelt_EMP", "Grenade_GrenadeBelt_OTC_EMP", "throw EMP grenade", 15.9),
    ("OCC_GrenadeBelt", "Grenade_GrenadeBelt_OCC", "throw blast grenade", 15.9),
    ("ODC_GrenadeBelt", "Grenade_GrenadeBelt_ODC", "throw stun grenade", 15.9),
    ("OMG_GrenadeBelt", "Grenade_GrenadeBelt_OMG", "throw necrobane grenade", 17.9),
)

_PROJECTILE_BASE = "OEGrenadeBeltsProjectileBase"


def _verb_op(def_name: str, projectile: str, label: str, range_: float) -> str:
    return f"""  <Operation Class="PatchOperationReplace">
    <xpath>{thing_xpath(def_name)}/verbs</xpath>
    <value>
      <verbs>
        <li Class="CombatExtended.VerbPropertiesCE">
          <label>{label}</label>
          <verbClass>CombatExtended.Verb_LaunchProjectileStaticCE</verbClass>
          <hasStandardCommand>true</hasStandardCommand>
          <onlyManualCast>True</onlyManualCast>
          <warmupTime>1.5</warmupTime>
          <range>{range_}</range>
          <minRange>3</minRange>
          <ai_IsBuildingDestroyer>true</ai_IsBuildingDestroyer>
          <soundCast>ThrowGrenade</soundCast>
          <drawHighlightWithLineOfSight>true</drawHighlightWithLineOfSight>
          <targetParams>
            <canTargetLocations>true</canTargetLocations>
          </targetParams>
          <ignorePartialLoSBlocker>true</ignorePartialLoSBlocker>
          <defaultProjectile>{projectile}</defaultProjectile>
          <rangedFireRulepack>Combat_RangedFire_Thrown</rangedFireRulepack>
        </li>
      </verbs>
    </value>
  </Operation>"""


def _projectile_class_op(xpath: str) -> str:
    return f"""  <Operation Class="PatchOperationAttributeSet">
    <xpath>{xpath}/projectile</xpath>
    <attribute>Class</attribute>
    <value>CombatExtended.ProjectilePropertiesCE</value>
  </Operation>"""


def emit_grenade_belt_xml() -> str:
    blocks = [
        wrap_optional_xpath(
            [_projectile_class_op(named_xpath(_PROJECTILE_BASE))],
            "",
            named_xpath(_PROJECTILE_BASE),
        )
    ]
    for def_name, projectile, label, range_ in GRENADE_BELTS:
        blocks.append(
            wrap_optional_def(
                [_verb_op(def_name, projectile, label, range_)],
                "",
                def_name,
            )
        )
        blocks.append(
            wrap_optional_def(
                [_projectile_class_op(thing_xpath(projectile))],
                "",
                projectile,
            )
        )
    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>\n'
