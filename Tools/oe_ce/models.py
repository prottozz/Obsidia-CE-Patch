from __future__ import annotations

from dataclasses import dataclass, field

from oe_ce.constants import BASE_CARTRIDGES, EMP_SIDE_TYPES


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
        out = list(BASE_CARTRIDGES)
        if self.class_name != "emp" and self.type in EMP_SIDE_TYPES:
            out.append("emp")
        return out

    def ammo_set_def(self) -> str:
        return f"AmmoSet_OE_{self.id}_{self.class_name}"

    def ammo_def(self, cartridge: str) -> str:
        return f"Ammo_OE_{self.id}_{self.class_name}_{cartridge}"

    def bullet_def(self, cartridge: str) -> str:
        return f"Bullet_OE_{self.id}_{self.class_name}_{cartridge}"


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
