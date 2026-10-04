from __future__ import annotations

from pathlib import Path

from oe_ce.models import Family, Member
from oe_ce.rungs import gun_stats
from oe_ce.scan_obsidia import thing_def_has_tools


def _xml_num(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    if value == int(value):
        return str(int(value))
    return format(value, "g")


def _tools_replace(member: Member) -> str:
    return f"""  <Operation Class="PatchOperationReplace">
    <xpath>Defs/ThingDef[defName="{member.def_name}"]/tools</xpath>
    <value>
      <tools>
        <li Class="CombatExtended.ToolCE">
          <label>stock</label>
          <capacities><li>Blunt</li></capacities>
          <power>6</power>
          <cooldownTime>2</cooldownTime>
          <armorPenetrationBlunt>0.5</armorPenetrationBlunt>
        </li>
        <li Class="CombatExtended.ToolCE">
          <label>barrel</label>
          <capacities><li>Poke</li></capacities>
          <power>6</power>
          <cooldownTime>2</cooldownTime>
          <armorPenetrationBlunt>0.5</armorPenetrationBlunt>
        </li>
      </tools>
    </value>
  </Operation>"""


def _make_gun_op(fam: Family, member: Member) -> str:
    stats = gun_stats(fam.type, member)
    burst_line = ""
    burst = stats.get("burst")
    if burst is not None and burst > 1:
        burst_line = f"\n      <burstShotCount>{_xml_num(burst)}</burstShotCount>"
    return f"""  <Operation Class="CombatExtended.PatchOperationMakeGunCECompatible">
    <defName>{member.def_name}</defName>
    <statBases>
      <Mass>{_xml_num(stats["mass"])}</Mass>
      <Bulk>{_xml_num(stats["bulk"])}</Bulk>
      <SwayFactor>{_xml_num(stats["sway"])}</SwayFactor>
      <ShotSpread>{_xml_num(stats["spread"])}</ShotSpread>
      <RangedWeapon_Cooldown>{_xml_num(stats["cooldown"])}</RangedWeapon_Cooldown>
    </statBases>
    <Properties>
      <recoilAmount>{_xml_num(stats["recoil"])}</recoilAmount>
      <verbClass>CombatExtended.Verb_ShootCE</verbClass>
      <hasStandardCommand>true</hasStandardCommand>
      <defaultProjectile>{fam.member_bullet_def(member, fam.default_cartridge())}</defaultProjectile>
      <warmupTime>{_xml_num(stats["warmup"])}</warmupTime>
      <range>{_xml_num(stats["range"])}</range>{burst_line}
    </Properties>
    <AmmoUser>
      <magazineSize>{_xml_num(stats["magazine"])}</magazineSize>
      <reloadTime>{_xml_num(stats["reload"])}</reloadTime>
      <ammoSet>{fam.member_ammo_set_def(member)}</ammoSet>
    </AmmoUser>
  </Operation>"""


def emit_gun_patches(families: list[Family], core: Path) -> str:
    blocks: list[str] = []
    for fam in families:
        for member in sorted(fam.members, key=lambda m: m.def_name):
            blocks.append(_make_gun_op(fam, member))
            if thing_def_has_tools(core, member.def_name):
                blocks.append(_tools_replace(member))
    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>'
