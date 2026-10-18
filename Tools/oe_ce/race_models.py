from __future__ import annotations

from dataclasses import dataclass, field

from oe_ce.race_analogues import race_stats


@dataclass
class RaceTool:
    label: str | None = None
    capacities: tuple[str, ...] = ()
    linked_body_parts_group: str | None = None
    power: float | None = None
    cooldown_time: float | None = None
    armor_penetration_sharp: float | None = None
    armor_penetration_blunt: float | None = None
    extra_xml: tuple[str, ...] = ()


@dataclass
class RaceMember:
    def_name: str
    analogue: str | None = None
    body_shape: str | None = None
    tools: list[RaceTool] | None = None


@dataclass
class RaceSet:
    id: str
    analogue: str
    body_shape: str | None = None
    members: list[RaceMember] = field(default_factory=list)

    def member_analogue(self, member: RaceMember) -> str:
        return member.analogue or self.analogue

    def member_body_shape(self, member: RaceMember) -> str:
        if member.body_shape:
            return member.body_shape
        if self.body_shape:
            return self.body_shape
        return race_stats(self.member_analogue(member)).body_shape


@dataclass
class RaceCatalog:
    sets: list[RaceSet] = field(default_factory=list)

    def entries(self) -> list[tuple[RaceSet, RaceMember]]:
        return [(s, m) for s in self.sets for m in s.members]
