from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ShieldMember:
    def_name: str
    rung: str | None = None
    mass: float | None = None
    bulk: float | None = None
    worn_bulk: float | None = None


@dataclass
class WornSet:
    id: str
    rung: str
    role: str
    plate: str
    members: list[ShieldMember] = field(default_factory=list)
    may_require: str | None = None

    def member_rung(self, member: ShieldMember) -> str:
        return member.rung or self.rung


@dataclass
class HandheldSet:
    id: str
    rung: str
    size: str
    members: list[ShieldMember] = field(default_factory=list)
    may_require: str | None = None

    def member_rung(self, member: ShieldMember) -> str:
        return member.rung or self.rung


@dataclass
class InnateSet:
    id: str
    analogue: str
    members: list[ShieldMember] = field(default_factory=list)
    may_require: str | None = None


@dataclass
class UpgradeSet:
    id: str
    factor: float
    members: list[ShieldMember] = field(default_factory=list)
    may_require: str | None = None


@dataclass
class ShieldCatalog:
    worn: list[WornSet] = field(default_factory=list)
    handheld: list[HandheldSet] = field(default_factory=list)
    innate: list[InnateSet] = field(default_factory=list)
    upgrades: list[UpgradeSet] = field(default_factory=list)

    def def_names(self) -> set[str]:
        names: set[str] = set()
        for group in (self.worn, self.handheld, self.innate, self.upgrades):
            for row in group:
                for member in row.members:
                    names.add(member.def_name)
        return names
