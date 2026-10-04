from __future__ import annotations

from dataclasses import dataclass, field

from oe_ce.constants import BASE_CARTRIDGES, CALIBER_BY_TYPE, ELEMENTAL_CLASSES, EMP_SIDE_TYPES


@dataclass
class Member:
    def_name: str
    rung: str
    range: float | None = None
    warmup: float | None = None
    burst: int | None = None
    magazine: int | None = None
    spread: float | None = None
    mass: float | None = None
    bulk: float | None = None
    ap_npc: bool = False


@dataclass
class Family:
    id: str
    type: str
    class_name: str
    experimental: bool = False
    cartridges: list[str] | None = None
    members: list[Member] = field(default_factory=list)

    def resolved_cartridges(self) -> list[str]:
        if self.cartridges is not None:
            return list(self.cartridges)
        if self.class_name in ELEMENTAL_CLASSES:
            return [self.class_name]
        out = list(BASE_CARTRIDGES)
        if self.type in EMP_SIDE_TYPES:
            out.append("emp")
        return out

    def default_cartridge(self) -> str:
        return self.resolved_cartridges()[0]

    def caliber(self) -> str:
        if self.experimental:
            return f"exp_{self.id}"
        return CALIBER_BY_TYPE[self.type]

    def display_label(self) -> str:
        if self.experimental:
            return self.id.replace("_", " ")
        return self.caliber()

    def ammo_set_def(self) -> str:
        return f"AmmoSet_OE_{self.caliber()}_{self.class_name}"

    def member_ammo_set_def(self, member: Member) -> str:
        return f"AmmoSet_OE_{member.def_name}"

    def ammo_def(self, cartridge: str) -> str:
        return f"Ammo_OE_{self.caliber()}_{self.class_name}_{cartridge}"

    def bullet_def(self, cartridge: str) -> str:
        return f"Bullet_OE_{self.caliber()}_{self.class_name}_{cartridge}"

    def member_bullet_def(self, member: Member, cartridge: str) -> str:
        return f"Bullet_OE_{member.def_name}_{cartridge}"


def unique_ammo_families(families: list[Family]) -> list[Family]:
    groups: dict[tuple[str, str], list[Family]] = {}
    for fam in families:
        groups.setdefault((fam.caliber(), fam.class_name), []).append(fam)
    out: list[Family] = []
    for _key, fams in sorted(groups.items()):
        carts: list[str] = []
        for fam in fams:
            for cart in fam.resolved_cartridges():
                if cart not in carts:
                    carts.append(cart)
        proto = sorted(fams, key=lambda f: f.id)[0]
        out.append(
            Family(
                id=proto.id,
                type=proto.type,
                class_name=proto.class_name,
                experimental=proto.experimental,
                cartridges=carts,
            )
        )
    return out


@dataclass
class Catalog:
    families: list[Family] = field(default_factory=list)
    melee: list[Member] = field(default_factory=list)

    def ranged_def_names(self) -> set[str]:
        names: set[str] = set()
        for fam in self.families:
            for m in fam.members:
                names.add(m.def_name)
        return names
