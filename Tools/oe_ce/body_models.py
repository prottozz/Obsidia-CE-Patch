from __future__ import annotations

from dataclasses import dataclass, field

BODY_ANALOGUES = frozenset({"beetle", "quadruped", "fingerspike", "scyther", "lancer", "human"})


@dataclass
class BodyEntry:
    def_name: str
    analogue: str
    may_require: str | None = None


@dataclass
class BodyCatalog:
    bodies: list[BodyEntry] = field(default_factory=list)
