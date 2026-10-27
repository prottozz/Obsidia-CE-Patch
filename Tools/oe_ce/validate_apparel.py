from __future__ import annotations

from collections import Counter

from oe_ce.apparel_models import ApparelCatalog
from oe_ce.apparel_rungs import apparel_stats
from oe_ce.constants import RUNGS
from oe_ce.scan_apparel import CoreApparel, is_excluded_apparel


def validate_apparel_catalog(
    cat: ApparelCatalog,
    core: dict[str, CoreApparel],
    *,
    present_packages: frozenset[str] = frozenset(),
) -> list[str]:
    errors: list[str] = []
    seen: list[str] = []
    resolved: dict[str, tuple[str, str]] = {}
    for kind, apparel_set, member in cat.entries():
        name = member.def_name
        rung = apparel_set.member_rung(member)
        seen.append(name)
        if rung not in RUNGS:
            errors.append(f"{name}: unknown rung {rung}")
        if is_excluded_apparel(name):
            errors.append(f"{name}: excluded apparel must not be catalogued")
            continue
        info = core.get(name)
        may_require = apparel_set.member_may_require(member)
        if info is None:
            if may_require and may_require not in present_packages:
                continue
            errors.append(f"{name}: not an in-scope apparel def")
        else:
            if info.kind != kind:
                errors.append(f"{name}: catalogued as {kind} but Core layer is {info.kind}")
            if info.package != may_require:
                errors.append(
                    f"{name}: mayRequire {may_require} but defined in {info.package or 'Core'}"
                )
        resolved[name] = (kind, rung)
    for name, count in Counter(seen).items():
        if count > 1:
            errors.append(f"duplicate apparel defName {name}")
    for missing in sorted(set(core) - set(seen)):
        errors.append(f"apparel defName not in catalog: {missing}")
    for name, (kind, rung) in sorted(resolved.items()):
        info = core.get(name)
        if info is None or info.concrete_parent not in resolved:
            continue
        parent_kind, parent_rung = resolved[info.concrete_parent]
        if rung not in RUNGS or parent_rung not in RUNGS:
            continue
        mine = apparel_stats(kind, rung).template
        theirs = apparel_stats(parent_kind, parent_rung).template
        if mine != theirs:
            errors.append(
                f"{name}: coverage template {mine} differs from inherited parent "
                f"{info.concrete_parent} ({theirs})"
            )
    return errors
