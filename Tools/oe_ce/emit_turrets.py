"""CE turret buildings, CE turret guns and the ammo-network feed patch."""

from __future__ import annotations

from oe_ce.emit_common import (
    ensure_node,
    format_num,
    set_stat,
    thing_xpath,
    wrap_optional_def,
)
from oe_ce.emit_guns import explosive_verb_lines
from oe_ce.explosive import Blast
from oe_ce.rungs import gun_stats
from oe_ce.scan_turrets import TurretScan
from oe_ce.turret_models import TurretCatalog, TurretGun

AMMO_NET = "OE_AmmoNet"
FEED_COMP = "ObsidiaCEAmmoNet.CompProperties_AmmoNetFeed"
TURRET_CLASS = "CombatExtended.Building_TurretGunCE"
REFILL_BELOW = 0.75  # Obsidia autoRefuelPercent on every OE_AmmoKit turret


def _patch(blocks: list[str]) -> str:
    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>\n'


def _wrap(ops: list[str], package: str | None, def_name: str) -> list[str]:
    return [wrap_optional_def(ops, package or "", def_name)]


def _replace_or_add(def_name: str, node: str, value: str) -> str:
    base = thing_xpath(def_name)
    return f"""  <Operation Class="PatchOperationConditional">
    <xpath>{base}/{node}</xpath>
    <match Class="PatchOperationReplace">
      <xpath>{base}/{node}</xpath>
      <value>
        <{node}>{value}</{node}>
      </value>
    </match>
    <nomatch Class="PatchOperationAdd">
      <xpath>{base}</xpath>
      <value>
        <{node}>{value}</{node}>
      </value>
    </nomatch>
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


def turret_gun_op(gun: TurretGun, burst: int | None, blast: Blast | None = None) -> str:
    fam = gun.family(burst)
    member = fam.members[0]
    stats = gun_stats(fam.type, member)
    burst_line = ""
    if stats.get("burst") and stats["burst"] > 1:
        burst_line = f"\n      <burstShotCount>{format_num(stats['burst'])}</burstShotCount>"
    ammo_block = ""
    if gun.magazine is not None:
        ammo_block = f"""
    <AmmoUser>
      <magazineSize>{format_num(gun.magazine)}</magazineSize>
      <reloadTime>{format_num(stats["reload"])}</reloadTime>
      <ammoSet>{fam.member_ammo_set_def(member)}</ammoSet>
    </AmmoUser>"""
    return f"""  <Operation Class="CombatExtended.PatchOperationMakeGunCECompatible">
    <defName>{gun.def_name}</defName>
    <statBases>
      <Mass>{format_num(stats["mass"])}</Mass>
      <SwayFactor>{format_num(stats["sway"])}</SwayFactor>
      <ShotSpread>{format_num(stats["spread"])}</ShotSpread>
      <RangedWeapon_Cooldown>{format_num(stats["cooldown"])}</RangedWeapon_Cooldown>
    </statBases>
    <Properties>
      <recoilAmount>{format_num(stats["recoil"])}</recoilAmount>
      <verbClass>CombatExtended.Verb_ShootCE</verbClass>
      <hasStandardCommand>true</hasStandardCommand>
      <defaultProjectile>{fam.member_bullet_def(member, fam.default_cartridge())}</defaultProjectile>
      <warmupTime>{format_num(stats["warmup"])}</warmupTime>
      <range>{format_num(stats["range"])}</range>{burst_line}{explosive_verb_lines(blast)}
      <recoilPattern>Mounted</recoilPattern>
    </Properties>{ammo_block}
    <FireModes>
      <aiAimMode>AimedShot</aiAimMode>
      <noSnapshot>true</noSnapshot>
      <noSingleShot>true</noSingleShot>
    </FireModes>
  </Operation>"""


def turret_building_ops(def_name: str) -> list[str]:
    ops = [
        _replace_or_add(def_name, "thingClass", TURRET_CLASS),
        ensure_node(def_name, "statBases"),
        set_stat(def_name, "statBases", "AimingAccuracy", 0.25),
        set_stat(def_name, "statBases", "ShootingAccuracyTurret", 0.5),
    ]
    # Ceiling turrets keep Obsidia's low fillPercent (they hang overhead).
    if "_Turret_Ceiling" not in def_name:
        fill = 0.9 if "_Turret_Big" in def_name else 0.85
        ops.append(_replace_or_add(def_name, "fillPercent", format_num(fill)))
    return ops + [
        # CE turrets never read CompRefuelable: drop it so no dead fuel bar and no
        # PipeSystem auto-link to a comp nothing consumes.
        _remove_if_present(f'{thing_xpath(def_name)}/comps/li[@Class="CompProperties_Refuelable"]'),
    ]


def emit_turret_xml(
    cat: TurretCatalog, scan: TurretScan, blasts: dict[str, Blast] | None = None
) -> str:
    blasts = blasts or {}
    blocks: list[str] = []
    for gun in sorted(cat.guns, key=lambda g: g.def_name):
        info = scan.guns.get(gun.def_name)
        burst = info.burst if info is not None else None
        op = turret_gun_op(gun, burst, blasts.get(gun.def_name))
        blocks += _wrap([op], gun.may_require, gun.def_name)
    for turret in sorted(scan.turrets.values(), key=lambda t: t.def_name):
        if turret.gun not in cat.by_name():
            continue
        blocks += _wrap(turret_building_ops(turret.def_name), turret.package, turret.def_name)
    return _patch(blocks)


def feed_comp_op(def_name: str, shots_per_unit: float) -> str:
    return f"""  <Operation Class="PatchOperationAdd">
    <xpath>{thing_xpath(def_name)}/comps</xpath>
    <value>
      <li Class="{FEED_COMP}">
        <pipeNet>{AMMO_NET}</pipeNet>
        <shotsPerUnit>{format_num(shots_per_unit)}</shotsPerUnit>
        <refillBelow>{format_num(REFILL_BELOW)}</refillBelow>
      </li>
    </value>
  </Operation>"""


def emit_ammo_net_xml(cat: TurretCatalog, scan: TurretScan) -> str:
    """Feed comp for every OE_AmmoKit turret. Lives in the VEF-gated load folder."""
    guns = cat.by_name()
    blocks: list[str] = []
    for turret in sorted(scan.turrets.values(), key=lambda t: t.def_name):
        gun = guns.get(turret.gun)
        if turret.tactical or turret.fuel_capacity is None or gun is None or gun.magazine is None:
            continue
        ops = [ensure_node(turret.def_name, "comps"), feed_comp_op(turret.def_name, gun.kit_shots)]
        blocks += _wrap(ops, turret.package, turret.def_name)
    return _patch(blocks)
