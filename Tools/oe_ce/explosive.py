"""Explosive CE projectiles for guns whose Obsidia projectile explodes (slice 10).

A gun is explosive iff its Obsidia defaultProjectile has explosionRadius > 0; the
weapon type does not decide. Numbers are CE-scaled: radius x0.7 capped, blast
damage x1.4 (small) / x3.0 (big, CE rockets are 150-340), element damage x1.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
import xml.etree.ElementTree as ET

from oe_ce.scan_obsidia import ThingDefIndex, walk_parents

BLAST_DEFS = frozenset({"OCCBlast", "Bomb"})
DOOMSDAY = "Projectile_DoomsdayRocket"
DEFAULT_BLAST_AMOUNT = 50.0  # vanilla Bomb default when Obsidia leaves it unset
RADIUS_FACTOR = 0.7
RADIUS_CAP = 3.5
DOOMSDAY_RADIUS_CAP = 6.0
BIG_RADIUS = 2.5  # Obsidia radius from which a blast counts as "big"
SMALL_BLAST_MULT = 1.4
BIG_BLAST_MULT = 3.0
ROCKET_SPEED = 40
BULLET_SPEED = 151
MIN_RANGE_RADIUS = 2.0
# CE Fragment_Small flies up to ~35 cells at fragSpeedFactor 1; distance scales with
# speed^2. Keep fragments within about FRAG_REACH x the blast radius.
CE_FRAG_MAX_CELLS = 35.0
FRAG_REACH = 2.5  # CE radius from which guns get minRange / building-destroyer AI

# cartridge -> (radius factor, damage factor) for ballistic families
CARTRIDGE_SHAPE = {
    "standard": (1.0, 1.0),
    "ap": (0.5, 0.9),
    "hp": (1.25, 1.1),
}


@dataclass(frozen=True)
class Blast:
    """Obsidia explosive projectile, as scanned."""

    damage_def: str
    amount: float | None
    radius: float
    thing_class: str | None

    @property
    def is_blast(self) -> bool:
        return self.damage_def in BLAST_DEFS

    @property
    def is_doomsday(self) -> bool:
        return self.thing_class == DOOMSDAY


@dataclass(frozen=True)
class ExplosiveRound:
    """One generated CE explosive bullet."""

    damage_def: str
    damage: int
    radius: float
    fragments: int
    speed: int
    frag_speed: float = 1.0


def _inherited_text(index: ThingDefIndex, el: ET.Element, path: str) -> str | None:
    for node in walk_parents(index, el):
        found = node.find(path)
        if found is not None and (found.text or "").strip():
            return found.text.strip()
    return None


def projectile_blast(index: ThingDefIndex, gun_def: str) -> Blast | None:
    gun = index.by_def.get(gun_def)
    if gun is None:
        return None
    proj_name = _inherited_text(index, gun, "verbs/li/defaultProjectile")
    proj = index.by_def.get(proj_name) if proj_name else None
    if proj is None:
        return None
    try:
        radius = float(_inherited_text(index, proj, "projectile/explosionRadius") or 0)
    except ValueError:
        return None
    if radius <= 0:
        return None
    amount_text = _inherited_text(index, proj, "projectile/damageAmountBase")
    return Blast(
        damage_def=_inherited_text(index, proj, "projectile/damageDef") or "Bomb",
        amount=float(amount_text) if amount_text else None,
        radius=radius,
        thing_class=_inherited_text(index, proj, "thingClass"),
    )


def ce_radius(blast: Blast, factor: float = 1.0) -> float:
    cap = DOOMSDAY_RADIUS_CAP if blast.is_doomsday else RADIUS_CAP
    return round(min(blast.radius * RADIUS_FACTOR * factor, cap), 1)


def ce_damage(blast: Blast, factor: float = 1.0) -> int:
    amount = blast.amount if blast.amount is not None else DEFAULT_BLAST_AMOUNT
    if blast.is_blast:
        mult = BIG_BLAST_MULT if blast.radius >= BIG_RADIUS else SMALL_BLAST_MULT
    else:
        mult = 1.0
    return max(1, int(round(amount * mult * factor)))


def fragments(blast: Blast, weapon_type: str) -> int:
    if not blast.is_blast or blast.radius < BIG_RADIUS:
        return 0
    if blast.is_doomsday:
        return 40
    return 30 if weapon_type == "rocket" else 20


def frag_speed_factor(radius: float) -> float:
    """fragSpeedFactor so fragments land within ~FRAG_REACH x radius cells."""
    return round(min(1.0, math.sqrt(FRAG_REACH * radius / CE_FRAG_MAX_CELLS)), 2)


def explosive_round(blast: Blast, weapon_type: str, cartridge: str) -> ExplosiveRound:
    radius_f, damage_f = CARTRIDGE_SHAPE.get(cartridge, (1.0, 1.0))
    damage_def = "EMP" if cartridge == "emp" else blast.damage_def
    radius = ce_radius(blast, radius_f)
    return ExplosiveRound(
        damage_def=damage_def,
        damage=ce_damage(blast, damage_f),
        radius=radius,
        fragments=fragments(blast, weapon_type) if cartridge != "emp" else 0,
        speed=ROCKET_SPEED if weapon_type == "rocket" else BULLET_SPEED,
        frag_speed=frag_speed_factor(radius),
    )


def min_range(blast: Blast) -> int | None:
    radius = ce_radius(blast)
    if radius < MIN_RANGE_RADIUS:
        return None
    return int(math.ceil(radius)) + 1
