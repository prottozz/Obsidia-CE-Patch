from __future__ import annotations

from pathlib import Path

import yaml

from oe_ce.constants import YAML_CLASS_FILES
from oe_ce.models import Catalog, Family, Member


def _member(raw: dict) -> Member:
    return Member(
        def_name=raw["defName"],
        rung=raw["rung"],
        range=raw.get("range"),
        warmup=raw.get("warmup"),
        burst=raw.get("burst"),
        magazine=raw.get("magazine"),
        spread=raw.get("spread"),
        mass=raw.get("mass"),
        bulk=raw.get("bulk"),
        ap_npc=bool(raw.get("ap_npc", False)),
    )


def load_catalog(catalog_dir: Path) -> Catalog:
    cat = Catalog()
    for class_name, filename in YAML_CLASS_FILES.items():
        path = catalog_dir / filename
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for raw in data.get("families") or []:
            cat.families.append(
                Family(
                    id=raw["id"],
                    type=raw["type"],
                    class_name=raw.get("class", class_name),
                    experimental=bool(raw.get("experimental", False)),
                    cartridges=raw.get("cartridges"),
                    members=[_member(m) for m in raw.get("members") or []],
                )
            )
    melee_path = catalog_dir / "melee.yaml"
    if melee_path.exists():
        data = yaml.safe_load(melee_path.read_text(encoding="utf-8")) or {}
        cat.melee = [_member(m) for m in data.get("members") or []]
    return cat
