from __future__ import annotations

from pathlib import Path

import yaml

from oe_ce.apparel_models import ApparelCatalog, ApparelMember, ApparelSet


def _sets(path: Path) -> list[ApparelSet]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: list[ApparelSet] = []
    for raw in data.get("sets") or []:
        out.append(
            ApparelSet(
                id=raw["id"],
                rung=raw["rung"],
                members=[
                    ApparelMember(
                        def_name=m["defName"],
                        rung=m.get("rung"),
                        may_require=m.get("mayRequire"),
                        mass=m.get("mass"),
                        bulk=m.get("bulk"),
                        worn_bulk=m.get("wornBulk"),
                    )
                    for m in raw.get("members") or []
                ],
                may_require=raw.get("mayRequire"),
            )
        )
    return out


def load_apparel_catalog(catalog_dir: Path) -> ApparelCatalog:
    return ApparelCatalog(
        armor=_sets(catalog_dir / "armor.yaml"),
        helmets=_sets(catalog_dir / "helmets.yaml"),
    )
