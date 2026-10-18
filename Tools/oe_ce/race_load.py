from __future__ import annotations

from pathlib import Path

import yaml

from oe_ce.race_models import RaceCatalog, RaceMember, RaceSet, RaceTool


def _tool(raw: dict) -> RaceTool:
    caps = raw.get("capacities") or []
    return RaceTool(
        label=raw.get("label"),
        capacities=tuple(caps),
        linked_body_parts_group=raw.get("linkedBodyPartsGroup"),
        power=raw.get("power"),
        cooldown_time=raw.get("cooldownTime"),
        armor_penetration_sharp=raw.get("armorPenetrationSharp"),
        armor_penetration_blunt=raw.get("armorPenetrationBlunt"),
    )


def _member(raw: dict) -> RaceMember:
    tools = raw.get("tools")
    return RaceMember(
        def_name=raw["defName"],
        analogue=raw.get("analogue"),
        body_shape=raw.get("bodyShape"),
        tools=[_tool(t) for t in tools] if tools is not None else None,
    )


def load_race_catalog(catalog_dir: Path) -> RaceCatalog:
    path = catalog_dir / "races.yaml"
    if not path.exists():
        return RaceCatalog()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sets: list[RaceSet] = []
    for raw in data.get("sets") or []:
        sets.append(
            RaceSet(
                id=raw["id"],
                analogue=raw["analogue"],
                body_shape=raw.get("bodyShape"),
                members=[_member(m) for m in raw.get("members") or []],
            )
        )
    return RaceCatalog(sets)
