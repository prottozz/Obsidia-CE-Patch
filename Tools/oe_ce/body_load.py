from __future__ import annotations

from pathlib import Path

import yaml

from oe_ce.body_models import BodyCatalog, BodyEntry


def load_body_catalog(catalog_dir: Path) -> BodyCatalog:
    path = catalog_dir / "bodies.yaml"
    if not path.exists():
        return BodyCatalog()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    bodies = [
        BodyEntry(
            def_name=raw["defName"],
            analogue=raw["analogue"],
            may_require=raw.get("mayRequire"),
        )
        for raw in data.get("bodies") or []
    ]
    return BodyCatalog(bodies)
