from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from oe_ce.models import Family, Member


@dataclass
class TurretGun:
    def_name: str
    type: str
    class_name: str
    rung: str
    magazine: int | None = None
    kit_shots: float | None = None
    may_require: str | None = None

    def family(self, burst: int | None = None) -> Family:
        """A one-member family so turret guns reuse the gun / ammo pipeline."""
        member = Member(def_name=self.def_name, rung=self.rung, burst=burst, magazine=self.magazine)
        return Family(
            id=f"turret_{self.def_name}",
            type=self.type,
            class_name=self.class_name,
            members=[member],
        )


@dataclass
class TurretCatalog:
    guns: list[TurretGun] = field(default_factory=list)

    def by_name(self) -> dict[str, TurretGun]:
        return {g.def_name: g for g in self.guns}


def load_turret_catalog(catalog_dir: Path) -> TurretCatalog:
    path = catalog_dir / "turrets.yaml"
    if not path.exists():
        return TurretCatalog()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    guns = [
        TurretGun(
            def_name=raw["defName"],
            type=raw["type"],
            class_name=raw["class"],
            rung=raw["rung"],
            magazine=raw.get("magazine"),
            kit_shots=raw.get("kitShots"),
            may_require=raw.get("mayRequire"),
        )
        for raw in data.get("guns") or []
    ]
    return TurretCatalog(guns=guns)
