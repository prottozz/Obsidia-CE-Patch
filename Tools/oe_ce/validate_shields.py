from __future__ import annotations

from collections import Counter

from oe_ce.constants import RUNGS
from oe_ce.scan_shields import HANDHELD, INNATE, UPGRADE, WORN, CoreShield
from oe_ce.shield_models import ShieldCatalog
from oe_ce.shield_rungs import HANDHELD_SIZES, INNATE_ENERGY, ROLES

PLATES = frozenset({"inherit", "emit", "skip"})


def _absent(may_require: str | None, present_packages: frozenset[str] | None) -> bool:
    """True when a row's optional package tree is not installed, so a scan miss is fine."""
    if not may_require or present_packages is None:
        return False
    return any(pkg.strip() not in present_packages for pkg in may_require.split(","))


def validate_shield_catalog(
    cat: ShieldCatalog,
    scanned: dict[str, CoreShield],
    armor_names: set[str],
    *,
    present_packages: frozenset[str] | None = frozenset(),
) -> list[str]:
    errors: list[str] = []
    seen: list[str] = []

    for worn in cat.worn:
        if worn.rung not in RUNGS:
            errors.append(f"{worn.id}: unknown rung {worn.rung}")
        if worn.role not in ROLES:
            errors.append(f"{worn.id}: unknown role {worn.role}")
        if worn.plate not in PLATES:
            errors.append(f"{worn.id}: unknown plate {worn.plate}")
        for member in worn.members:
            name = member.def_name
            seen.append(name)
            if member.rung is not None and member.rung not in RUNGS:
                errors.append(f"{name}: unknown rung {member.rung}")
            info = scanned.get(name)
            if info is None:
                if not _absent(worn.may_require, present_packages):
                    errors.append(f"{name}: not in scan")
                continue
            if info.kind != WORN:
                errors.append(f"{name}: catalogued as worn but scan kind is {info.kind}")
            expected = True if worn.role == "guardian" else False
            if info.blocks_ranged is not None and info.blocks_ranged != expected:
                errors.append(
                    f"{name}: role {worn.role} disagrees with blocksRangedWeapons="
                    f"{info.blocks_ranged}"
                )
            parent = info.concrete_parent
            if worn.plate == "inherit" and parent not in armor_names:
                errors.append(f"{name}: plate inherit requires a parent in armor.yaml")
            if worn.plate == "emit" and parent in armor_names:
                errors.append(f"{name}: plate emit would double-plate parent {parent}")

    for hand in cat.handheld:
        if hand.rung not in RUNGS:
            errors.append(f"{hand.id}: unknown rung {hand.rung}")
        if hand.size not in HANDHELD_SIZES:
            errors.append(f"{hand.id}: unknown size {hand.size}")
        for member in hand.members:
            seen.append(member.def_name)
            info = scanned.get(member.def_name)
            if info is None:
                if not _absent(hand.may_require, present_packages):
                    errors.append(f"{member.def_name}: not in scan")
            elif info.kind != HANDHELD:
                errors.append(
                    f"{member.def_name}: catalogued as handheld but scan kind is {info.kind}"
                )

    for innate in cat.innate:
        if innate.analogue not in INNATE_ENERGY:
            errors.append(f"{innate.id}: unknown analogue {innate.analogue}")
        for member in innate.members:
            seen.append(member.def_name)
            info = scanned.get(member.def_name)
            if info is None:
                if not _absent(innate.may_require, present_packages):
                    errors.append(f"{member.def_name}: not in scan")
            elif info.kind != INNATE:
                errors.append(
                    f"{member.def_name}: catalogued as innate but scan kind is {info.kind}"
                )

    for upgrade in cat.upgrades:
        if not isinstance(upgrade.factor, (int, float)) or isinstance(upgrade.factor, bool):
            errors.append(f"{upgrade.id}: factor is not a number")
        for member in upgrade.members:
            seen.append(member.def_name)
            info = scanned.get(member.def_name)
            if info is None:
                if not _absent(upgrade.may_require, present_packages):
                    errors.append(f"{member.def_name}: not in scan")
            elif info.kind != UPGRADE:
                errors.append(
                    f"{member.def_name}: catalogued as upgrade but scan kind is {info.kind}"
                )

    for name, count in Counter(seen).items():
        if count > 1:
            errors.append(f"duplicate shield defName {name}")
    for missing in sorted(set(scanned) - set(seen)):
        errors.append(f"{missing}: not in catalog")
    return errors
