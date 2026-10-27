from __future__ import annotations

from dataclasses import dataclass, field

from oe_ce.apparel_rungs import ARMOR, HELMET


@dataclass
class ApparelMember:
    def_name: str
    rung: str | None = None
    may_require: str | None = None
    # Optional per-piece overrides of the rung's Mass / Bulk / WornBulk
    # (kid gear). A mass override also drops the rung's carry offsets.
    mass: float | None = None
    bulk: float | None = None
    worn_bulk: float | None = None


@dataclass
class ApparelSet:
    id: str
    rung: str
    members: list[ApparelMember] = field(default_factory=list)
    may_require: str | None = None

    def member_rung(self, member: ApparelMember) -> str:
        return member.rung or self.rung

    def member_may_require(self, member: ApparelMember) -> str | None:
        return member.may_require or self.may_require


@dataclass
class ApparelCatalog:
    armor: list[ApparelSet] = field(default_factory=list)
    helmets: list[ApparelSet] = field(default_factory=list)

    def entries(self) -> list[tuple[str, ApparelSet, ApparelMember]]:
        out = [(ARMOR, s, m) for s in self.armor for m in s.members]
        out += [(HELMET, s, m) for s in self.helmets for m in s.members]
        return out
