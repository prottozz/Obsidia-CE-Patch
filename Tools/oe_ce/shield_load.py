from __future__ import annotations

from pathlib import Path

import yaml

from oe_ce.shield_models import (
    HandheldSet,
    InnateSet,
    ShieldCatalog,
    ShieldMember,
    UpgradeSet,
    WornSet,
)


def _members(raw_list: list | None) -> list[ShieldMember]:
    out: list[ShieldMember] = []
    for raw in raw_list or []:
        out.append(
            ShieldMember(
                def_name=raw["defName"],
                rung=raw.get("rung"),
                mass=raw.get("mass"),
                bulk=raw.get("bulk"),
                worn_bulk=raw.get("wornBulk"),
            )
        )
    return out


def load_shield_catalog(catalog_dir: Path) -> ShieldCatalog:
    path = catalog_dir / "shields.yaml"
    if not path.exists():
        return ShieldCatalog()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    worn = [
        WornSet(
            id=raw["id"],
            rung=raw["rung"],
            role=raw["role"],
            plate=raw["plate"],
            members=_members(raw.get("members")),
            may_require=raw.get("mayRequire"),
        )
        for raw in data.get("worn") or []
    ]
    handheld = [
        HandheldSet(
            id=raw["id"],
            rung=raw["rung"],
            size=raw["size"],
            members=_members(raw.get("members")),
            may_require=raw.get("mayRequire"),
        )
        for raw in data.get("handheld") or []
    ]
    innate = [
        InnateSet(
            id=raw["id"],
            analogue=raw["analogue"],
            members=_members(raw.get("members")),
            may_require=raw.get("mayRequire"),
        )
        for raw in data.get("innate") or []
    ]
    upgrades = [
        UpgradeSet(
            id=raw["id"],
            factor=raw["factor"],
            members=_members(raw.get("members")),
            may_require=raw.get("mayRequire"),
        )
        for raw in data.get("upgrades") or []
    ]
    return ShieldCatalog(worn=worn, handheld=handheld, innate=innate, upgrades=upgrades)
