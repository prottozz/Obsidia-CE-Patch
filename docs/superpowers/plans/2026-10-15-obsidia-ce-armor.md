# Slice 2 Core Armor and Helmets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Patch every in-scope Obsidia Expansion Core combat body armor and helmet onto Combat Extended sharp / blunt / heat ratings, bulk, carry capacity and `PartialArmorExt` coverage, driven by a set catalog and an armor rung table.

**Architecture:** Two new YAML catalogs (`catalog/armor.yaml`, `catalog/helmets.yaml`) group Core apparel into named sets with rungs. A new scanner reads Obsidia `1.6/Core` Apparel XML, classifies pieces as armor (Shell layer) or helmet (Overhead layer), drops excluded defs, and records concrete parents. A validator fails on any coverage gap. A new emitter writes conditional replace-or-add XPath patches into committed `Patches/Apparel/OE_Armor.xml` and `Patches/Apparel/OE_Helmets.xml`. Slice 1 gun / ammo / melee code is untouched apart from one helper rename and the `generate.py` wiring.

**Tech Stack:** Python 3.10+, PyYAML, pytest, RimWorld 1.6 XML patch operations, Combat Extended `PartialArmorExt`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-10-04-obsidia-ce-armor-design.md`.
- Work on branch `feat/slice-2-armor` (worktree `C:\Projects\Obsidia-CE-Patch\.worktrees\feat-slice-1-core-weapons`, currently checked out on that branch). Do not commit to `main`. Do not push.
- RimWorld 1.6 only. `packageId` stays `prottozz.ObsidiaCEPatch`. XML only, no Harmony.
- In scope: Core combat body armor and helmets in `Defs/ThingDefs_Misc/Apparel`.
- Never catalog or patch: `OE_Uniform_Military`, `OE_Uniform_Worker`; defNames containing `Shield`, `Barrier`, `Grenadier`; defNames starting `Grenade_`; `ODC_Helmet_Miner`, `ODC_Helmet_Constructor`, `ODC_Helmet_Medic`, `ODC_Helmet_Trader`, `ODC_Helmet_Beastmaster`, `EGO_Helmet_Exohelm_Worker`, `EGO_Armor_Shell_Worker`.
- Armor uses the slice 1 rung **names** with a separate stat table. Never call `gun_stats()` for apparel.
- `otc` armor is strictly below `occ`; `otc_t2` is strictly below `occ_reforge`.
- CE reference points (sharp / blunt): recon 16 / 34, marine 20 / 45, cataphract 28 / 60. Helmets recon 12 / 26, marine 16 / 36, cataphract 22 / 50. Heat on the vanilla 0–2 scale.
- Body armor gets `CarryWeight` / `CarryBulk` offsets; helmets get none.
- A catalogued child whose concrete parent is also catalogued gets stats but no `PartialArmorExt`, and must share the parent's coverage template.
- No new `Defs/`. Do not touch recipes, `recipeUsers`, traders, pawnKinds, or Obsidia's other `equippedStatOffsets`.
- Generated XML is UTF-8, committed, reproducible (sorted by defName). Never hand-edit generated XML.
- Obsidia source tree: `C:\Projects\Assistant\294100\2519492373\1.6\Core` (override with env `OBSIDIA_CORE`).
- Test command (PowerShell): `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests -v`. Git / pytest on this machine need the shell run outside the sandbox.

## File map

| Path | Responsibility |
|---|---|
| `Tools/oe_ce/apparel_rungs.py` | Armor / helmet rung tables, coverage templates, `apparel_stats()` |
| `Tools/oe_ce/scan_apparel.py` | Exclude rules, Core apparel scan, armor/helmet classification, concrete parents |
| `Tools/oe_ce/scan_obsidia.py` | Rename `_walk_parents` → `walk_parents` so the apparel scanner can reuse it |
| `Tools/oe_ce/apparel_models.py` | `ApparelMember`, `ApparelSet`, `ApparelCatalog` |
| `Tools/oe_ce/apparel_load.py` | Read `armor.yaml` / `helmets.yaml` |
| `Tools/oe_ce/validate_apparel.py` | Coverage, duplicate, exclude, kind and template checks |
| `Tools/oe_ce/emit_apparel.py` | Patch XML for one apparel kind |
| `Tools/oe_ce/generate.py` | Require Apparel dir, validate, write `Patches/Apparel/*` |
| `catalog/armor.yaml`, `catalog/helmets.yaml` | Source of truth for sets and rungs |
| `Patches/Apparel/OE_Armor.xml`, `Patches/Apparel/OE_Helmets.xml` | Generated, committed |
| `Tools/tests/test_apparel_*.py`, `Tools/tests/test_scan_apparel.py`, `Tools/tests/test_emit_apparel.py`, `Tools/tests/test_generate.py` | Tests |

---

### Task 1: Armor rung tables and coverage templates

**Files:**
- Create: `Tools/oe_ce/apparel_rungs.py`
- Test: `Tools/tests/test_apparel_rungs.py`

**Interfaces:**
- Consumes: `oe_ce.constants.RUNGS`
- Produces:
  - `ARMOR = "armor"`, `HELMET = "helmet"`, `APPAREL_KINDS = (ARMOR, HELMET)`
  - `CoverageRow(mult: float, parts: tuple[str, ...])` (frozen dataclass)
  - `ArmorStats(sharp, blunt, heat, mass, bulk, worn_bulk, carry_weight: float | None, carry_bulk: float | None, template: str)` (frozen dataclass)
  - `COVERAGE: dict[str, tuple[CoverageRow, ...]]` keyed `armor_light`, `armor_marine`, `armor_heavy`, `helmet_light`, `helmet_marine`, `helmet_heavy`
  - `ARMOR_BY_RUNG`, `HELMET_BY_RUNG: dict[str, ArmorStats]`, one entry per rung in `RUNGS`
  - `apparel_stats(kind: str, rung: str) -> ArmorStats` (raises `ValueError` on unknown kind, `KeyError` on unknown rung)

- [ ] **Step 1: Write the failing test**

```python
# Tools/tests/test_apparel_rungs.py
import pytest

from oe_ce.apparel_rungs import (
    ARMOR,
    ARMOR_BY_RUNG,
    COVERAGE,
    HELMET,
    HELMET_BY_RUNG,
    apparel_stats,
)
from oe_ce.constants import RUNGS


def test_every_rung_has_armor_and_helmet_rows():
    assert set(ARMOR_BY_RUNG) == set(RUNGS)
    assert set(HELMET_BY_RUNG) == set(RUNGS)


def test_occ_is_ce_marine():
    occ = apparel_stats(ARMOR, "occ")
    assert (occ.sharp, occ.blunt, occ.heat) == (20, 45, 0.54)
    assert occ.template == "armor_marine"
    helm = apparel_stats(HELMET, "occ")
    assert (helm.sharp, helm.blunt) == (16, 36)
    assert helm.template == "helmet_marine"


def test_otc_strictly_below_occ_at_both_tiers():
    for kind in (ARMOR, HELMET):
        otc = apparel_stats(kind, "otc")
        occ = apparel_stats(kind, "occ")
        assert otc.sharp < occ.sharp and otc.blunt < occ.blunt
        otc_t2 = apparel_stats(kind, "otc_t2")
        occ_reforge = apparel_stats(kind, "occ_reforge")
        assert otc_t2.sharp < occ_reforge.sharp and otc_t2.blunt < occ_reforge.blunt


def test_armor_ladder_order():
    ladder = ["proto", "otc", "occ", "oec", "oe", "odc_t2", "odc_t3", "odc_t4", "omg"]
    sharps = [apparel_stats(ARMOR, r).sharp for r in ladder]
    assert sharps == sorted(sharps)
    assert len(set(sharps)) == len(sharps)
    assert apparel_stats(ARMOR, "omc").sharp == apparel_stats(ARMOR, "occ").sharp
    assert apparel_stats(ARMOR, "odc_t4").sharp == 28
    assert apparel_stats(ARMOR, "heroic") == apparel_stats(ARMOR, "odc_t4")
    assert apparel_stats(ARMOR, "bio_t3") == apparel_stats(ARMOR, "odc_t3")
    assert apparel_stats(ARMOR, "mech") == apparel_stats(ARMOR, "omc")


def test_body_armor_carries_helmets_do_not():
    for rung in RUNGS:
        assert apparel_stats(ARMOR, rung).carry_weight is not None
        assert apparel_stats(HELMET, rung).carry_weight is None
    assert apparel_stats(ARMOR, "occ").carry_weight == 80
    assert apparel_stats(ARMOR, "odc_t4").carry_bulk == 20


def test_templates_exist_and_match_kind():
    for rung in RUNGS:
        assert apparel_stats(ARMOR, rung).template.startswith("armor_")
        assert apparel_stats(HELMET, rung).template.startswith("helmet_")
        assert apparel_stats(ARMOR, rung).template in COVERAGE
        assert apparel_stats(HELMET, rung).template in COVERAGE
    arm_parts = {p for row in COVERAGE["armor_light"] for p in row.parts}
    assert arm_parts == {"Neck", "Arm", "Leg"}
    helm_parts = {p for row in COVERAGE["helmet_marine"] for p in row.parts}
    assert "Arm" not in helm_parts and "Eye" in helm_parts


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        apparel_stats("cloak", "occ")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_apparel_rungs.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'oe_ce.apparel_rungs'`

- [ ] **Step 3: Write the implementation**

```python
# Tools/oe_ce/apparel_rungs.py
from __future__ import annotations

from dataclasses import dataclass

from oe_ce.constants import RUNGS

ARMOR = "armor"
HELMET = "helmet"
APPAREL_KINDS = (ARMOR, HELMET)


@dataclass(frozen=True)
class CoverageRow:
    mult: float
    parts: tuple[str, ...]


@dataclass(frozen=True)
class ArmorStats:
    sharp: float
    blunt: float
    heat: float
    mass: float
    bulk: float
    worn_bulk: float
    carry_weight: float | None
    carry_bulk: float | None
    template: str


# Obsidia pieces never cover hands or feet, so CE's Hand rows are dropped.
COVERAGE: dict[str, tuple[CoverageRow, ...]] = {
    "armor_light": (
        CoverageRow(0.60, ("Neck",)),
        CoverageRow(0.80, ("Arm",)),
        CoverageRow(0.90, ("Leg",)),
    ),
    "armor_marine": (
        CoverageRow(0.80, ("Neck",)),
        CoverageRow(0.90, ("Arm",)),
    ),
    "armor_heavy": (CoverageRow(0.90, ("Neck",)),),
    "helmet_light": (
        CoverageRow(0.70, ("Eye",)),
        CoverageRow(0.50, ("Nose", "Jaw")),
    ),
    "helmet_marine": (CoverageRow(0.80, ("Eye", "Nose")),),
    "helmet_heavy": (CoverageRow(0.90, ("Eye",)),),
}


def _armor(
    sharp: float,
    blunt: float,
    heat: float,
    mass: float,
    carry_weight: float,
    carry_bulk: float,
    template: str,
    bulk: float = 100,
    worn_bulk: float = 15,
) -> ArmorStats:
    return ArmorStats(
        sharp, blunt, heat, mass, bulk, worn_bulk, carry_weight, carry_bulk, f"armor_{template}"
    )


def _helmet(
    sharp: float, blunt: float, heat: float, mass: float, bulk: float, template: str
) -> ArmorStats:
    return ArmorStats(sharp, blunt, heat, mass, bulk, 1, None, None, f"helmet_{template}")


ARMOR_BY_RUNG: dict[str, ArmorStats] = {
    "proto": _armor(16, 34, 0.46, 30, 50, 8, "light", bulk=80, worn_bulk=12),
    "otc": _armor(17, 38, 0.50, 40, 65, 9, "light", bulk=90, worn_bulk=13),
    "odc_t1": _armor(20, 45, 0.54, 50, 80, 10, "marine"),
    "oec": _armor(21, 47, 0.55, 52, 80, 10, "marine"),
    "oe": _armor(22, 49, 0.56, 55, 85, 12, "marine"),
    "odc_t2": _armor(24, 52, 0.58, 60, 90, 15, "heavy"),
    "odc_t3": _armor(26, 56, 0.60, 70, 95, 18, "heavy"),
    "odc_t4": _armor(28, 60, 0.62, 80, 100, 20, "heavy"),
    "omg": _armor(30, 64, 0.65, 80, 100, 20, "heavy"),
}

HELMET_BY_RUNG: dict[str, ArmorStats] = {
    "proto": _helmet(12, 26, 0.46, 3.0, 4, "light"),
    "otc": _helmet(14, 31, 0.50, 4.0, 4.5, "light"),
    "odc_t1": _helmet(16, 36, 0.54, 4.8, 5, "marine"),
    "oec": _helmet(17, 38, 0.55, 5.0, 5, "marine"),
    "oe": _helmet(18, 40, 0.56, 5.2, 5, "marine"),
    "odc_t2": _helmet(19, 43, 0.58, 5.6, 5.5, "heavy"),
    "odc_t3": _helmet(20, 46, 0.60, 6.0, 6, "heavy"),
    "odc_t4": _helmet(22, 50, 0.62, 6.6, 6, "heavy"),
    "omg": _helmet(24, 54, 0.65, 6.6, 6, "heavy"),
}

for _table in (ARMOR_BY_RUNG, HELMET_BY_RUNG):
    _table["occ"] = _table["odc_t1"]
    _table["omc"] = _table["odc_t1"]
    _table["mech"] = _table["odc_t1"]
    _table["otc_t2"] = _table["odc_t2"]
    for _alias in ("occ_reforge", "omc_mod", "oec_t2", "cac_t1", "bio_t3"):
        _table[_alias] = _table["odc_t3"]
    for _alias in ("heroic", "trophy", "cac_t2", "bio_t4"):
        _table[_alias] = _table["odc_t4"]
    assert set(_table) == set(RUNGS)


def apparel_stats(kind: str, rung: str) -> ArmorStats:
    if kind == ARMOR:
        return ARMOR_BY_RUNG[rung]
    if kind == HELMET:
        return HELMET_BY_RUNG[rung]
    raise ValueError(f"unknown apparel kind {kind}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_apparel_rungs.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add Tools/oe_ce/apparel_rungs.py Tools/tests/test_apparel_rungs.py
git commit -m "feat: add CE armor and helmet rung tables"
```

---

### Task 2: Scan Core apparel

**Files:**
- Modify: `Tools/oe_ce/scan_obsidia.py` (rename `_walk_parents` → `walk_parents`, both call sites in `weapon_projectile_graphic`)
- Create: `Tools/oe_ce/scan_apparel.py`
- Test: `Tools/tests/test_scan_apparel.py`

**Interfaces:**
- Consumes: `ARMOR`, `HELMET` from Task 1; `ThingDefIndex` from `oe_ce.scan_obsidia`
- Produces:
  - `walk_parents(index: ThingDefIndex, start: ET.Element) -> list[ET.Element]` in `oe_ce.scan_obsidia`
  - `is_excluded_apparel(def_name: str) -> bool`
  - `CoreApparel(def_name: str, kind: str, concrete_parent: str | None = None)` (frozen dataclass)
  - `scan_core_apparel(core: Path) -> dict[str, CoreApparel]` — non-abstract, non-excluded defs whose nearest `apparel/layers` has `Shell` (armor) or `Overhead` (helmet). Raises `FileNotFoundError` mentioning "apparel" if `Defs/ThingDefs_Misc/Apparel` is missing.

- [ ] **Step 1: Write the failing test**

```python
# Tools/tests/test_scan_apparel.py
import os
from pathlib import Path

import pytest

from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.constants import DEFAULT_OBSIDIA_CORE
from oe_ce.scan_apparel import is_excluded_apparel, scan_core_apparel

CORE = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))

FIXTURE = """
  <ThingDef Name="OEArmorBase" Abstract="True">
    <apparel><layers><li>Middle</li><li>Shell</li></layers></apparel>
  </ThingDef>
  <ThingDef Name="OEHelmetBase" Abstract="True">
    <apparel><layers><li>Overhead</li></layers></apparel>
  </ThingDef>
  <ThingDef Name="OEUniformBase" Abstract="True">
    <apparel><layers><li>OnSkin</li></layers></apparel>
  </ThingDef>
  <ThingDef Name="OCCArmorMod" ParentName="OEArmorBase">
    <defName>OCC_Armor_M</defName>
  </ThingDef>
  <ThingDef ParentName="OCCArmorMod">
    <defName>OCC_Armor_M_Spacer</defName>
  </ThingDef>
  <ThingDef ParentName="OCCArmorMod">
    <defName>OCC_Armor_M_Shield</defName>
  </ThingDef>
  <ThingDef ParentName="OEHelmetBase">
    <defName>OCC_Helmet</defName>
  </ThingDef>
  <ThingDef ParentName="OEHelmetBase">
    <defName>ODC_Helmet_Miner</defName>
  </ThingDef>
  <ThingDef ParentName="OEUniformBase">
    <defName>OE_Uniform_Military</defName>
  </ThingDef>
  <ThingDef>
    <defName>Grenade_Armor_OTC_Acid</defName>
  </ThingDef>
"""


def _write_apparel(core: Path, body: str) -> Path:
    apparel = core / "Defs" / "ThingDefs_Misc" / "Apparel"
    apparel.mkdir(parents=True, exist_ok=True)
    (apparel / "Fixture.xml").write_text(
        f'<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n{body}\n</Defs>\n',
        encoding="utf-8",
    )
    return core


def test_excludes():
    for name in (
        "OTC_Armor_M_Grenadier_Fire",
        "OES_Armor_Barrier",
        "OCC_Armor_M_Shield",
        "Grenade_Armor_OTC_Acid",
        "ODC_Helmet_Beastmaster",
        "EGO_Armor_Shell_Worker",
        "OE_Uniform_Worker",
    ):
        assert is_excluded_apparel(name), name
    for name in ("OCC_Armor", "ODC_Armor_Recon_Smoker", "OMG_Trophy_Helmet_Hellrain"):
        assert not is_excluded_apparel(name), name


def test_scan_classifies_and_records_concrete_parent(tmp_path):
    core = _write_apparel(tmp_path, FIXTURE)
    found = scan_core_apparel(core)
    assert set(found) == {"OCC_Armor_M", "OCC_Armor_M_Spacer", "OCC_Helmet"}
    assert found["OCC_Armor_M"].kind == ARMOR
    assert found["OCC_Armor_M"].concrete_parent is None
    assert found["OCC_Armor_M_Spacer"].kind == ARMOR
    assert found["OCC_Armor_M_Spacer"].concrete_parent == "OCC_Armor_M"
    assert found["OCC_Helmet"].kind == HELMET


def test_scan_fails_without_apparel_dir(tmp_path):
    with pytest.raises(FileNotFoundError, match="apparel"):
        scan_core_apparel(tmp_path)


def test_real_core_apparel_counts():
    found = scan_core_apparel(CORE)
    armor = {n for n, a in found.items() if a.kind == ARMOR}
    helmets = {n for n, a in found.items() if a.kind == HELMET}
    assert len(armor) == 32
    assert len(helmets) == 32
    assert "EGO_Armor_Suit" in armor
    assert "OMG_Trophy_Helmet_Forgemind" in helmets
    assert found["OCC_Armor_M_Spacer"].concrete_parent == "OCC_Armor_M"
    assert "OCC_Armor_M_Shield" not in found
    assert "OE_Uniform_Military" not in found
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_scan_apparel.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'oe_ce.scan_apparel'`

- [ ] **Step 3: Make `walk_parents` public in `Tools/oe_ce/scan_obsidia.py`**

Rename the definition:

```python
def walk_parents(index: ThingDefIndex, start: ET.Element) -> list[ET.Element]:
```

and both uses inside `weapon_projectile_graphic`:

```python
    for el in walk_parents(idx, gun):
```

```python
    for el in walk_parents(idx, proj):
```

- [ ] **Step 4: Write `Tools/oe_ce/scan_apparel.py`**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.scan_obsidia import ThingDefIndex, walk_parents

APPAREL_EXCLUDE_EXACT = frozenset(
    {
        "OE_Uniform_Military",
        "OE_Uniform_Worker",
        "ODC_Helmet_Miner",
        "ODC_Helmet_Constructor",
        "ODC_Helmet_Medic",
        "ODC_Helmet_Trader",
        "ODC_Helmet_Beastmaster",
        "EGO_Helmet_Exohelm_Worker",
        "EGO_Armor_Shell_Worker",
    }
)
APPAREL_EXCLUDE_SUBSTRINGS = ("Shield", "Barrier", "Grenadier")
APPAREL_EXCLUDE_PREFIXES = ("Grenade_",)


def is_excluded_apparel(def_name: str) -> bool:
    if def_name in APPAREL_EXCLUDE_EXACT:
        return True
    if def_name.startswith(APPAREL_EXCLUDE_PREFIXES):
        return True
    return any(part in def_name for part in APPAREL_EXCLUDE_SUBSTRINGS)


@dataclass(frozen=True)
class CoreApparel:
    def_name: str
    kind: str
    concrete_parent: str | None = None


def _apparel_dir(core: Path) -> Path:
    root = core / "Defs" / "ThingDefs_Misc" / "Apparel"
    if not root.is_dir():
        raise FileNotFoundError(f"Obsidia Core apparel dir missing: {root}")
    return root


def _index(core: Path) -> ThingDefIndex:
    by_def: dict[str, ET.Element] = {}
    by_name: dict[str, ET.Element] = {}
    for path in sorted(_apparel_dir(core).rglob("*.xml")):
        for el in ET.parse(path).getroot():
            if el.tag != "ThingDef":
                continue
            def_name = (el.findtext("defName") or "").strip()
            if def_name:
                by_def[def_name] = el
            name = el.get("Name")
            if name:
                by_name[name] = el
    return ThingDefIndex(by_def=by_def, by_name=by_name)


def _layers(index: ThingDefIndex, el: ET.Element) -> list[str]:
    for node in walk_parents(index, el):
        layers = node.find("apparel/layers")
        if layers is not None:
            return [(li.text or "").strip() for li in layers.findall("li")]
    return []


def _kind(layers: list[str]) -> str | None:
    if "Shell" in layers:
        return ARMOR
    if "Overhead" in layers:
        return HELMET
    return None


def _concrete_parent(index: ThingDefIndex, el: ET.Element) -> str | None:
    parent_name = el.get("ParentName")
    if not parent_name:
        return None
    parent = index.by_name.get(parent_name)
    if parent is None or parent.get("Abstract") == "True":
        return None
    return (parent.findtext("defName") or "").strip() or None


def scan_core_apparel(core: Path) -> dict[str, CoreApparel]:
    index = _index(core)
    out: dict[str, CoreApparel] = {}
    for def_name, el in sorted(index.by_def.items()):
        if el.get("Abstract") == "True" or is_excluded_apparel(def_name):
            continue
        kind = _kind(_layers(index, el))
        if kind is None:
            continue
        out[def_name] = CoreApparel(def_name, kind, _concrete_parent(index, el))
    return out
```

- [ ] **Step 5: Run the new tests and the slice 1 scan tests**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_scan_apparel.py Tools/tests/test_scan.py -v`
Expected: all passed (4 new + 3 existing)

- [ ] **Step 6: Commit**

```bash
git add Tools/oe_ce/scan_obsidia.py Tools/oe_ce/scan_apparel.py Tools/tests/test_scan_apparel.py
git commit -m "feat: scan Core combat armor and helmets"
```

---

### Task 3: Apparel catalog model, loader and validator

**Files:**
- Create: `Tools/oe_ce/apparel_models.py`
- Create: `Tools/oe_ce/apparel_load.py`
- Create: `Tools/oe_ce/validate_apparel.py`
- Test: `Tools/tests/test_apparel_catalog.py`

**Interfaces:**
- Consumes: `ARMOR`, `HELMET`, `apparel_stats` (Task 1); `CoreApparel`, `is_excluded_apparel` (Task 2); `RUNGS`
- Produces:
  - `ApparelMember(def_name: str, rung: str | None = None)`
  - `ApparelSet(id: str, rung: str, members: list[ApparelMember])` with `member_rung(member) -> str`
  - `ApparelCatalog(armor: list[ApparelSet], helmets: list[ApparelSet])` with `entries() -> list[tuple[str, ApparelSet, ApparelMember]]` (kind first)
  - `load_apparel_catalog(catalog_dir: Path) -> ApparelCatalog` (missing YAML file → empty list)
  - `validate_apparel_catalog(cat: ApparelCatalog, core: dict[str, CoreApparel]) -> list[str]`

YAML shape (`catalog/armor.yaml` and `catalog/helmets.yaml`):

```yaml
sets:
  - id: occ
    rung: occ
    members:
      - defName: OCC_Armor
      - defName: OCC_Armor_M
        rung: occ_reforge
```

- [ ] **Step 1: Write the failing test**

```python
# Tools/tests/test_apparel_catalog.py
from oe_ce.apparel_load import load_apparel_catalog
from oe_ce.apparel_models import ApparelCatalog, ApparelMember, ApparelSet
from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.scan_apparel import CoreApparel
from oe_ce.validate_apparel import validate_apparel_catalog

CORE = {
    "OCC_Armor": CoreApparel("OCC_Armor", ARMOR),
    "OCC_Armor_M": CoreApparel("OCC_Armor_M", ARMOR),
    "OCC_Armor_M_Spacer": CoreApparel("OCC_Armor_M_Spacer", ARMOR, "OCC_Armor_M"),
    "OCC_Helmet": CoreApparel("OCC_Helmet", HELMET),
}


def _armor_set(spacer_rung: str = "occ_reforge") -> ApparelSet:
    return ApparelSet(
        "occ",
        "occ",
        [
            ApparelMember("OCC_Armor"),
            ApparelMember("OCC_Armor_M", "occ_reforge"),
            ApparelMember("OCC_Armor_M_Spacer", spacer_rung),
        ],
    )


def _good() -> ApparelCatalog:
    return ApparelCatalog(
        armor=[_armor_set()],
        helmets=[ApparelSet("occ", "occ", [ApparelMember("OCC_Helmet")])],
    )


def test_good_catalog_is_clean():
    assert validate_apparel_catalog(_good(), CORE) == []


def test_member_rung_override():
    s = _armor_set()
    assert s.member_rung(s.members[0]) == "occ"
    assert s.member_rung(s.members[1]) == "occ_reforge"


def test_missing_core_piece_is_error():
    cat = ApparelCatalog(armor=[_armor_set()], helmets=[])
    errs = validate_apparel_catalog(cat, CORE)
    assert "Core apparel defName not in catalog: OCC_Helmet" in errs


def test_duplicate_is_error():
    cat = _good()
    cat.armor.append(ApparelSet("dupe", "occ", [ApparelMember("OCC_Armor")]))
    errs = validate_apparel_catalog(cat, CORE)
    assert "duplicate apparel defName OCC_Armor" in errs


def test_excluded_is_error():
    cat = _good()
    cat.armor[0].members.append(ApparelMember("OCC_Armor_M_Shield"))
    errs = validate_apparel_catalog(cat, CORE)
    assert any("OCC_Armor_M_Shield" in e and "excluded" in e for e in errs)


def test_kind_mismatch_is_error():
    cat = ApparelCatalog(
        armor=[_armor_set(), ApparelSet("occ_h", "occ", [ApparelMember("OCC_Helmet")])],
        helmets=[],
    )
    errs = validate_apparel_catalog(cat, CORE)
    assert any("OCC_Helmet" in e and "catalogued as armor" in e for e in errs)


def test_child_template_must_match_parent():
    cat = ApparelCatalog(
        armor=[_armor_set(spacer_rung="occ")],
        helmets=[ApparelSet("occ", "occ", [ApparelMember("OCC_Helmet")])],
    )
    errs = validate_apparel_catalog(cat, CORE)
    assert any("OCC_Armor_M_Spacer" in e and "coverage template" in e for e in errs)


def test_unknown_rung_is_error():
    cat = _good()
    cat.helmets[0].members[0].rung = "legendary"
    errs = validate_apparel_catalog(cat, CORE)
    assert "OCC_Helmet: unknown rung legendary" in errs


def test_load_reads_both_files(tmp_path):
    (tmp_path / "armor.yaml").write_text(
        "sets:\n"
        "  - id: occ\n"
        "    rung: occ\n"
        "    members:\n"
        "      - defName: OCC_Armor\n"
        "      - defName: OCC_Armor_M\n"
        "        rung: occ_reforge\n",
        encoding="utf-8",
    )
    (tmp_path / "helmets.yaml").write_text(
        "sets:\n"
        "  - id: occ\n"
        "    rung: occ\n"
        "    members:\n"
        "      - defName: OCC_Helmet\n",
        encoding="utf-8",
    )
    cat = load_apparel_catalog(tmp_path)
    assert [m.def_name for m in cat.armor[0].members] == ["OCC_Armor", "OCC_Armor_M"]
    assert cat.armor[0].members[1].rung == "occ_reforge"
    assert cat.armor[0].members[0].rung is None
    assert cat.helmets[0].members[0].def_name == "OCC_Helmet"
    kinds = [k for k, _s, _m in cat.entries()]
    assert kinds == [ARMOR, ARMOR, HELMET]


def test_load_missing_files_is_empty(tmp_path):
    cat = load_apparel_catalog(tmp_path)
    assert cat.armor == [] and cat.helmets == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_apparel_catalog.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'oe_ce.apparel_load'`

- [ ] **Step 3: Write `Tools/oe_ce/apparel_models.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field

from oe_ce.apparel_rungs import ARMOR, HELMET


@dataclass
class ApparelMember:
    def_name: str
    rung: str | None = None


@dataclass
class ApparelSet:
    id: str
    rung: str
    members: list[ApparelMember] = field(default_factory=list)

    def member_rung(self, member: ApparelMember) -> str:
        return member.rung or self.rung


@dataclass
class ApparelCatalog:
    armor: list[ApparelSet] = field(default_factory=list)
    helmets: list[ApparelSet] = field(default_factory=list)

    def entries(self) -> list[tuple[str, ApparelSet, ApparelMember]]:
        out = [(ARMOR, s, m) for s in self.armor for m in s.members]
        out += [(HELMET, s, m) for s in self.helmets for m in s.members]
        return out
```

- [ ] **Step 4: Write `Tools/oe_ce/apparel_load.py`**

```python
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
                    ApparelMember(def_name=m["defName"], rung=m.get("rung"))
                    for m in raw.get("members") or []
                ],
            )
        )
    return out


def load_apparel_catalog(catalog_dir: Path) -> ApparelCatalog:
    return ApparelCatalog(
        armor=_sets(catalog_dir / "armor.yaml"),
        helmets=_sets(catalog_dir / "helmets.yaml"),
    )
```

- [ ] **Step 5: Write `Tools/oe_ce/validate_apparel.py`**

```python
from __future__ import annotations

from collections import Counter

from oe_ce.apparel_models import ApparelCatalog
from oe_ce.apparel_rungs import apparel_stats
from oe_ce.constants import RUNGS
from oe_ce.scan_apparel import CoreApparel, is_excluded_apparel


def validate_apparel_catalog(cat: ApparelCatalog, core: dict[str, CoreApparel]) -> list[str]:
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
        if info is None:
            errors.append(f"{name}: not an in-scope Core apparel def")
        elif info.kind != kind:
            errors.append(f"{name}: catalogued as {kind} but Core layer is {info.kind}")
        resolved[name] = (kind, rung)
    for name, count in Counter(seen).items():
        if count > 1:
            errors.append(f"duplicate apparel defName {name}")
    for missing in sorted(set(core) - set(seen)):
        errors.append(f"Core apparel defName not in catalog: {missing}")
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
```

- [ ] **Step 6: Run test to verify it passes**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_apparel_catalog.py -v`
Expected: 10 passed

- [ ] **Step 7: Commit**

```bash
git add Tools/oe_ce/apparel_models.py Tools/oe_ce/apparel_load.py Tools/oe_ce/validate_apparel.py Tools/tests/test_apparel_catalog.py
git commit -m "feat: load and validate the armor and helmet catalog"
```

---

### Task 4: Emit apparel patches

**Files:**
- Create: `Tools/oe_ce/emit_apparel.py`
- Test: `Tools/tests/test_emit_apparel.py`

**Interfaces:**
- Consumes: `ARMOR`, `HELMET`, `COVERAGE`, `apparel_stats` (Task 1); `CoreApparel` (Task 2); `ApparelSet`, `ApparelMember` (Task 3)
- Produces: `emit_apparel_xml(sets: list[ApparelSet], kind: str, core: dict[str, CoreApparel]) -> str` — a full `<Patch>` document, ops grouped per defName in defName order.

Per member, in this order:
1. Conditional: if `statBases` is missing, add an empty `<statBases />`.
2. For `ArmorRating_Sharp`, `ArmorRating_Blunt`, `ArmorRating_Heat`, `Mass`, `Bulk`, `WornBulk`: conditional replace-or-add under `statBases`.
3. Body armor only: ensure `equippedStatOffsets`, then replace-or-add `CarryWeight`, `CarryBulk`.
4. Unless the member's concrete parent is in the same `sets`: `PatchOperationAddModExtension` with `CombatExtended.PartialArmorExt` from `COVERAGE[stats.template]` (one Sharp and one Blunt row per coverage row).

- [ ] **Step 1: Write the failing test**

```python
# Tools/tests/test_emit_apparel.py
import xml.etree.ElementTree as ET

from oe_ce.apparel_models import ApparelMember, ApparelSet
from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.emit_apparel import emit_apparel_xml
from oe_ce.scan_apparel import CoreApparel

CORE = {
    "OCC_Armor": CoreApparel("OCC_Armor", ARMOR),
    "OCC_Armor_M": CoreApparel("OCC_Armor_M", ARMOR),
    "OCC_Armor_M_Spacer": CoreApparel("OCC_Armor_M_Spacer", ARMOR, "OCC_Armor_M"),
    "OCC_Helmet": CoreApparel("OCC_Helmet", HELMET),
}


def test_occ_armor_gets_marine_stats_carry_and_coverage():
    xml = emit_apparel_xml([ApparelSet("occ", "occ", [ApparelMember("OCC_Armor")])], ARMOR, CORE)
    assert '<xpath>Defs/ThingDef[defName="OCC_Armor"]/statBases/ArmorRating_Sharp</xpath>' in xml
    assert "<ArmorRating_Sharp>20</ArmorRating_Sharp>" in xml
    assert "<ArmorRating_Blunt>45</ArmorRating_Blunt>" in xml
    assert "<ArmorRating_Heat>0.54</ArmorRating_Heat>" in xml
    assert "<Mass>50</Mass>" in xml
    assert "<Bulk>100</Bulk>" in xml
    assert "<WornBulk>15</WornBulk>" in xml
    assert "<CarryWeight>80</CarryWeight>" in xml
    assert "<CarryBulk>10</CarryBulk>" in xml
    assert "CombatExtended.PartialArmorExt" in xml
    assert "<li>Arm</li>" in xml
    assert "<ArmorRating_Sharp>0.90</ArmorRating_Sharp>" in xml


def test_missing_stat_nodes_are_added_not_assumed():
    xml = emit_apparel_xml([ApparelSet("occ", "occ", [ApparelMember("OCC_Armor")])], ARMOR, CORE)
    assert "<statBases />" in xml
    assert "<equippedStatOffsets />" in xml
    assert 'Class="PatchOperationConditional"' in xml
    assert '<nomatch Class="PatchOperationAdd">' in xml
    assert '<match Class="PatchOperationReplace">' in xml


def test_helmet_uses_helmet_template_and_no_carry():
    xml = emit_apparel_xml([ApparelSet("occ", "occ", [ApparelMember("OCC_Helmet")])], HELMET, CORE)
    assert "<ArmorRating_Sharp>16</ArmorRating_Sharp>" in xml
    assert "<ArmorRating_Blunt>36</ArmorRating_Blunt>" in xml
    assert "<li>Eye</li>" in xml
    assert "<li>Arm</li>" not in xml
    assert "CarryWeight" not in xml
    assert "equippedStatOffsets" not in xml


def test_child_of_catalogued_parent_gets_stats_but_no_second_extension():
    s = ApparelSet(
        "occ",
        "occ_reforge",
        [ApparelMember("OCC_Armor_M"), ApparelMember("OCC_Armor_M_Spacer")],
    )
    xml = emit_apparel_xml([s], ARMOR, CORE)
    assert xml.count("PatchOperationAddModExtension") == 1
    assert '<xpath>Defs/ThingDef[defName="OCC_Armor_M"]</xpath>' in xml
    assert (
        '<xpath>Defs/ThingDef[defName="OCC_Armor_M_Spacer"]/statBases/ArmorRating_Sharp</xpath>'
        in xml
    )
    assert "<ArmorRating_Sharp>26</ArmorRating_Sharp>" in xml


def test_output_is_valid_sorted_patch():
    s = ApparelSet(
        "occ",
        "occ",
        [ApparelMember("OCC_Armor_M", "occ_reforge"), ApparelMember("OCC_Armor")],
    )
    xml = emit_apparel_xml([s], ARMOR, CORE)
    root = ET.fromstring(xml.split("?>", 1)[1])
    assert root.tag == "Patch"
    assert xml.index('defName="OCC_Armor"]') < xml.index('defName="OCC_Armor_M"]')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_emit_apparel.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'oe_ce.emit_apparel'`

- [ ] **Step 3: Write `Tools/oe_ce/emit_apparel.py`**

```python
from __future__ import annotations

from oe_ce.apparel_models import ApparelSet
from oe_ce.apparel_rungs import ARMOR, COVERAGE, apparel_stats
from oe_ce.scan_apparel import CoreApparel


def _num(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    if value == int(value):
        return str(int(value))
    return format(value, "g")


def _base(def_name: str) -> str:
    return f'Defs/ThingDef[defName="{def_name}"]'


def _ensure_node(def_name: str, node: str) -> str:
    base = _base(def_name)
    return f"""  <Operation Class="PatchOperationConditional">
    <xpath>{base}/{node}</xpath>
    <nomatch Class="PatchOperationAdd">
      <xpath>{base}</xpath>
      <value>
        <{node} />
      </value>
    </nomatch>
  </Operation>"""


def _set_stat(def_name: str, node: str, stat: str, value: float) -> str:
    base = _base(def_name)
    text = _num(value)
    return f"""  <Operation Class="PatchOperationConditional">
    <xpath>{base}/{node}/{stat}</xpath>
    <match Class="PatchOperationReplace">
      <xpath>{base}/{node}/{stat}</xpath>
      <value>
        <{stat}>{text}</{stat}>
      </value>
    </match>
    <nomatch Class="PatchOperationAdd">
      <xpath>{base}/{node}</xpath>
      <value>
        <{stat}>{text}</{stat}>
      </value>
    </nomatch>
  </Operation>"""


def _partial_armor(def_name: str, template: str) -> str:
    rows: list[str] = []
    for row in COVERAGE[template]:
        parts = "\n".join(f"              <li>{part}</li>" for part in row.parts)
        for stat in ("ArmorRating_Sharp", "ArmorRating_Blunt"):
            rows.append(
                f"""          <li>
            <{stat}>{row.mult:.2f}</{stat}>
            <parts>
{parts}
            </parts>
          </li>"""
            )
    inner = "\n".join(rows)
    return f"""  <Operation Class="PatchOperationAddModExtension">
    <xpath>{_base(def_name)}</xpath>
    <value>
      <li Class="CombatExtended.PartialArmorExt">
        <stats>
{inner}
        </stats>
      </li>
    </value>
  </Operation>"""


def _member_ops(kind: str, def_name: str, rung: str, inherits_coverage: bool) -> list[str]:
    stats = apparel_stats(kind, rung)
    ops = [_ensure_node(def_name, "statBases")]
    for stat, value in (
        ("ArmorRating_Sharp", stats.sharp),
        ("ArmorRating_Blunt", stats.blunt),
        ("ArmorRating_Heat", stats.heat),
        ("Mass", stats.mass),
        ("Bulk", stats.bulk),
        ("WornBulk", stats.worn_bulk),
    ):
        ops.append(_set_stat(def_name, "statBases", stat, value))
    if kind == ARMOR and stats.carry_weight is not None and stats.carry_bulk is not None:
        ops.append(_ensure_node(def_name, "equippedStatOffsets"))
        ops.append(_set_stat(def_name, "equippedStatOffsets", "CarryWeight", stats.carry_weight))
        ops.append(_set_stat(def_name, "equippedStatOffsets", "CarryBulk", stats.carry_bulk))
    if not inherits_coverage:
        ops.append(_partial_armor(def_name, stats.template))
    return ops


def emit_apparel_xml(sets: list[ApparelSet], kind: str, core: dict[str, CoreApparel]) -> str:
    catalogued = {m.def_name for s in sets for m in s.members}
    rows = sorted((m.def_name, s.member_rung(m)) for s in sets for m in s.members)
    blocks: list[str] = []
    for def_name, rung in rows:
        info = core.get(def_name)
        inherits = info is not None and info.concrete_parent in catalogued
        blocks.extend(_member_ops(kind, def_name, rung, inherits))
    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>\n'
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_emit_apparel.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add Tools/oe_ce/emit_apparel.py Tools/tests/test_emit_apparel.py
git commit -m "feat: emit CE armor and helmet patches"
```

---

### Task 5: Full catalog, generator wiring, committed XML

**Files:**
- Create: `catalog/armor.yaml`
- Create: `catalog/helmets.yaml`
- Modify: `Tools/oe_ce/generate.py`
- Modify: `Tools/tests/test_generate.py`
- Create: `Tools/tests/test_apparel_coverage.py`
- Generated: `Patches/Apparel/OE_Armor.xml`, `Patches/Apparel/OE_Helmets.xml`

**Interfaces:**
- Consumes: everything from Tasks 1–4
- Produces: `generate(root)` additionally fails without `Defs/ThingDefs_Misc/Apparel`, includes apparel validation errors in its error list, and writes the two apparel patch files.

- [ ] **Step 1: Write the failing coverage test**

```python
# Tools/tests/test_apparel_coverage.py
import os
from pathlib import Path

from oe_ce.apparel_load import load_apparel_catalog
from oe_ce.apparel_rungs import ARMOR, HELMET, apparel_stats
from oe_ce.constants import DEFAULT_OBSIDIA_CORE
from oe_ce.scan_apparel import scan_core_apparel
from oe_ce.validate_apparel import validate_apparel_catalog

ROOT = Path(__file__).resolve().parents[2]
CORE = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))


def _rung(sets, def_name):
    for s in sets:
        for m in s.members:
            if m.def_name == def_name:
                return s.member_rung(m)
    raise KeyError(def_name)


def test_core_apparel_fully_catalogued():
    cat = load_apparel_catalog(ROOT / "catalog")
    errs = validate_apparel_catalog(cat, scan_core_apparel(CORE))
    assert errs == [], "\n".join(errs)


def test_catalog_keeps_otc_below_occ():
    cat = load_apparel_catalog(ROOT / "catalog")
    pairs = [
        (ARMOR, cat.armor, "OTC_Armor", "OCC_Armor"),
        (ARMOR, cat.armor, "OTC_Armor_M", "OCC_Armor_M"),
        (HELMET, cat.helmets, "OTC_Helmet", "OCC_Helmet"),
        (HELMET, cat.helmets, "OTC_Helmet_M", "OCC_Helmet_M"),
    ]
    for kind, sets, otc, occ in pairs:
        weak = apparel_stats(kind, _rung(sets, otc))
        strong = apparel_stats(kind, _rung(sets, occ))
        assert weak.sharp < strong.sharp, (otc, occ)
        assert weak.blunt < strong.blunt, (otc, occ)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_apparel_coverage.py -v`
Expected: FAIL — `test_core_apparel_fully_catalogued` lists 64 `Core apparel defName not in catalog: ...` lines; `test_catalog_keeps_otc_below_occ` raises `KeyError: 'OTC_Armor'`

- [ ] **Step 3: Write `catalog/armor.yaml`**

```yaml
# Core combat body armor. Rung names match the gun catalog; numbers come from
# Tools/oe_ce/apparel_rungs.py, not the gun table.
sets:
  - id: proto
    rung: proto
    members:
      - defName: OE_Armor_Proto
  - id: occ
    rung: occ
    members:
      - defName: OCC_Armor
      - defName: OCC_Armor_M
        rung: occ_reforge
      - defName: OCC_Armor_M_Spacer
        rung: occ_reforge
  - id: otc
    rung: otc
    members:
      - defName: OTC_Armor
      - defName: OTC_Armor_M
        rung: otc_t2
      - defName: OTC_Armor_M_Spacer
        rung: otc_t2
  - id: omc
    rung: omc
    members:
      - defName: OMC_Armor
      - defName: OMC_Armor_M
        rung: omc_mod
      - defName: OMC_Armor_M_Spacer
        rung: omc_mod
      - defName: OMC_Armor_M_Smoker
        rung: omc_mod
  - id: odc_nomad
    rung: odc_t1
    members:
      - defName: ODC_Armor_Nomad
  - id: odc_recon
    rung: odc_t2
    members:
      - defName: ODC_Armor_Recon
      - defName: ODC_Armor_Recon_Spacer
      - defName: ODC_Armor_Recon_Smoker
  - id: odc_duelist
    rung: odc_t3
    members:
      - defName: ODC_Armor_Duelist
      - defName: ODC_Armor_Duelist_Spacer
      - defName: ODC_Armor_Duelist_Smoker
  - id: odc_stalker
    rung: odc_t4
    members:
      - defName: ODC_Armor_Stalker_Direwolf
      - defName: ODC_Armor_Stalker_Raptor
      - defName: ODC_Armor_Stalker_Ogren
      - defName: ODC_Armor_Stalker_Tionant
  - id: cac_light
    rung: cac_t1
    members:
      - defName: CAC_LightArmor
      - defName: CAC_LightArmor_Smoker
  - id: cac_heavy
    rung: cac_t2
    members:
      - defName: CAC_HeavyArmor
      - defName: CAC_HeavyArmor_Smoker
  - id: ego
    rung: bio_t3
    members:
      - defName: EGO_Armor_Suit
      - defName: EGO_Armor_Carapace
      - defName: EGO_Armor_Shell_Melee
        rung: bio_t4
      - defName: EGO_Armor_Shell_Ranged
        rung: bio_t4
  - id: omg
    rung: omg
    members:
      - defName: OMG_Armor_Corsair
      - defName: OMG_Armor_Demolition
```

- [ ] **Step 4: Write `catalog/helmets.yaml`**

```yaml
# Core combat helmets. Set ids match catalog/armor.yaml where a kit has both.
sets:
  - id: proto
    rung: proto
    members:
      - defName: OE_Helmet_Proto
  - id: occ
    rung: occ
    members:
      - defName: OCC_Helmet
      - defName: OCC_Helmet_M
        rung: occ_reforge
      - defName: OCC_Helmet_M_Spacer
        rung: occ_reforge
      - defName: OCC_Helmet_M_Melee
        rung: occ_reforge
      - defName: OCC_Helmet_M_Ranged
        rung: occ_reforge
  - id: otc
    rung: otc
    members:
      - defName: OTC_Helmet
      - defName: OTC_Helmet_M
        rung: otc_t2
      - defName: OTC_Helmet_M_Spacer
        rung: otc_t2
      - defName: OTC_Helmet_M_Melee
        rung: otc_t2
      - defName: OTC_Helmet_M_Ranged
        rung: otc_t2
  - id: omc
    rung: omc
    members:
      - defName: OMC_Helmet
      - defName: OMC_Helmet_M
        rung: omc_mod
      - defName: OMC_Helmet_M_Spacer
        rung: omc_mod
      - defName: OMC_Helmet_M_Melee
        rung: omc_mod
      - defName: OMC_Helmet_M_Ranged
        rung: omc_mod
  - id: odc_nomad
    rung: odc_t1
    members:
      - defName: ODC_Helmet_Nomad
  - id: odc_recon
    rung: odc_t2
    members:
      - defName: ODC_Helmet_Recon
      - defName: ODC_Helmet_Spacer
  - id: odc_duelist
    rung: odc_t3
    members:
      - defName: ODC_Helmet_Duelist
  - id: cac_light
    rung: cac_t1
    members:
      - defName: CAC_LightHelmet
  - id: cac_heavy
    rung: cac_t2
    members:
      - defName: CAC_HeavyHelmet
  - id: ego
    rung: bio_t3
    members:
      - defName: EGO_Helmet_Mask
      - defName: EGO_Helmet_Helm
      - defName: EGO_Helmet_Exohelm_Melee
        rung: bio_t4
      - defName: EGO_Helmet_Exohelm_Ranged
        rung: bio_t4
  - id: oes
    rung: heroic
    members:
      - defName: OES_Helmet_Melee
      - defName: OES_Helmet_Ranged
  - id: omg
    rung: omg
    members:
      - defName: OMG_Helmet_Classic
      - defName: OMG_Trophy_Helmet_Forgemind
      - defName: OMG_Trophy_Helmet_Hellrain
      - defName: OMG_Trophy_Helmet_Orbicore
```

- [ ] **Step 5: Run coverage test to verify it passes**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_apparel_coverage.py -v`
Expected: 2 passed. If `test_core_apparel_fully_catalogued` still lists defNames, Obsidia Core changed since this plan was written: add each listed in-scope def to the matching set (or extend the exclude list in `scan_apparel.py` only if it is clearly a uniform / shield / barrier / grenadier / job piece), then re-run.

- [ ] **Step 6: Write the failing generator tests in `Tools/tests/test_generate.py`**

Replace the whole file with:

```python
import shutil
from pathlib import Path

import pytest

from oe_ce.generate import generate

ROOT = Path(__file__).resolve().parents[2]


def _write_minimal_core(core: Path, *, with_apparel: bool = True) -> None:
    weapons = core / "Defs" / "ThingDefs_Misc" / "Weapons"
    weapons.mkdir(parents=True)
    (weapons / "Rifles.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef>
    <defName>OE_Rifle</defName>
    <verbs><li /></verbs>
    <tools><li /></tools>
    <weaponTags><li>OE_ProtoGun</li></weaponTags>
  </ThingDef>
  <ThingDef>
    <defName>OCC_Rifle</defName>
    <verbs><li /></verbs>
    <tools><li /></tools>
    <weaponTags><li>OE_OccGun</li></weaponTags>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    pawnkinds = core / "Defs" / "PawnKinds"
    pawnkinds.mkdir(parents=True)
    if not with_apparel:
        return
    apparel = core / "Defs" / "ThingDefs_Misc" / "Apparel"
    apparel.mkdir(parents=True)
    (apparel / "Armor.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef Name="OEArmorBase" Abstract="True">
    <apparel><layers><li>Middle</li><li>Shell</li></layers></apparel>
  </ThingDef>
  <ThingDef Name="OCCArmorMod" ParentName="OEArmorBase">
    <defName>OCC_Armor_M</defName>
  </ThingDef>
  <ThingDef ParentName="OCCArmorMod">
    <defName>OCC_Armor_M_Shield</defName>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )


def test_generate_cerberus_files(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "fake_core"
    _write_minimal_core(core)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    monkeypatch.setenv("OE_CE_ALLOW_PARTIAL", "1")
    generate(tmp_path)
    ammo = (tmp_path / "Defs" / "Ammo" / "OE_Ammo.xml").read_text(encoding="utf-8")
    guns = (tmp_path / "Patches" / "Weapons" / "OE_Ranged.xml").read_text(encoding="utf-8")
    assert "Ammo_OE_rifle_ballistic_standard" in ammo
    assert "AmmoSet_OE_OE_Rifle" in ammo
    assert "OE_Rifle" in guns
    assert "OCC_Rifle" in guns


def test_generate_writes_apparel_patches(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "fake_core"
    _write_minimal_core(core)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    monkeypatch.setenv("OE_CE_ALLOW_PARTIAL", "1")
    generate(tmp_path)
    armor = (tmp_path / "Patches" / "Apparel" / "OE_Armor.xml").read_text(encoding="utf-8")
    helmets = (tmp_path / "Patches" / "Apparel" / "OE_Helmets.xml").read_text(encoding="utf-8")
    assert 'defName="OCC_Armor_M"]' in armor
    assert "OCC_Armor_M_Shield" not in armor
    assert "CombatExtended.PartialArmorExt" in armor
    assert 'defName="OCC_Helmet"]' in helmets
    assert "CarryWeight" not in helmets


def test_generate_fails_without_core_weapons(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "empty_core"
    core.mkdir()
    (core / "Defs" / "PawnKinds").mkdir(parents=True)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    with pytest.raises(FileNotFoundError, match="weapons"):
        generate(tmp_path)


def test_generate_fails_without_core_apparel(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "no_apparel_core"
    _write_minimal_core(core, with_apparel=False)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    with pytest.raises(FileNotFoundError, match="apparel"):
        generate(tmp_path)
```

- [ ] **Step 7: Run to verify the new generator tests fail**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_generate.py -v`
Expected: `test_generate_writes_apparel_patches` FAIL (`FileNotFoundError` on `OE_Armor.xml`) and `test_generate_fails_without_core_apparel` FAIL (`DID NOT RAISE`); the other two pass.

- [ ] **Step 8: Replace `Tools/oe_ce/generate.py`**

```python
from __future__ import annotations

import os
import sys
from pathlib import Path

from oe_ce.apparel_load import load_apparel_catalog
from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.constants import DEFAULT_OBSIDIA_CORE
from oe_ce.emit_ammo import emit_ammo_xml
from oe_ce.emit_apparel import emit_apparel_xml
from oe_ce.emit_guns import emit_gun_patches
from oe_ce.emit_melee import emit_melee_xml
from oe_ce.emit_pawnkinds import emit_pawnkind_xml
from oe_ce.emit_recipes import emit_recipe_xml
from oe_ce.load import load_catalog
from oe_ce.scan_apparel import scan_core_apparel
from oe_ce.scan_obsidia import scan_core_ranged
from oe_ce.validate import validate_catalog
from oe_ce.validate_apparel import validate_apparel_catalog


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _require_core_dirs(core: Path) -> None:
    weapons = core / "Defs" / "ThingDefs_Misc" / "Weapons"
    pawnkinds = core / "Defs" / "PawnKinds"
    apparel = core / "Defs" / "ThingDefs_Misc" / "Apparel"
    if not weapons.is_dir():
        raise FileNotFoundError(f"Obsidia Core weapons dir missing: {weapons}")
    if not pawnkinds.is_dir():
        raise FileNotFoundError(f"Obsidia Core PawnKinds dir missing: {pawnkinds}")
    if not apparel.is_dir():
        raise FileNotFoundError(f"Obsidia Core apparel dir missing: {apparel}")


def generate(root: Path) -> None:
    cat = load_catalog(root / "catalog")
    apparel = load_apparel_catalog(root / "catalog")
    core = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))
    _require_core_dirs(core)
    core_apparel = scan_core_apparel(core)
    errors = validate_catalog(cat, scan_core_ranged(core))
    errors += validate_apparel_catalog(apparel, core_apparel)
    if errors and os.environ.get("OE_CE_ALLOW_PARTIAL") != "1":
        for msg in errors:
            print(msg, file=sys.stderr)
        sys.exit(1)

    _write(root / "Defs" / "Ammo" / "OE_Ammo.xml", emit_ammo_xml(cat.families, core))
    _write(
        root / "Defs" / "RecipeDefs" / "OE_AmmoRecipes.xml",
        emit_recipe_xml(cat.families),
    )
    _write(
        root / "Patches" / "Weapons" / "OE_Ranged.xml",
        emit_gun_patches(cat.families, core),
    )
    _write(
        root / "Patches" / "Weapons" / "OE_Melee.xml",
        emit_melee_xml(cat.melee),
    )
    _write(
        root / "Patches" / "PawnKinds" / "OE_Loadouts.xml",
        emit_pawnkind_xml(core, cat.families),
    )
    _write(
        root / "Patches" / "Apparel" / "OE_Armor.xml",
        emit_apparel_xml(apparel.armor, ARMOR, core_apparel),
    )
    _write(
        root / "Patches" / "Apparel" / "OE_Helmets.xml",
        emit_apparel_xml(apparel.helmets, HELMET, core_apparel),
    )
```

- [ ] **Step 9: Regenerate against real Core and run the full suite**

Run:

```powershell
Remove-Item Env:OE_CE_ALLOW_PARTIAL -ErrorAction SilentlyContinue
python Tools/generate_ce_patch.py
$env:PYTHONPATH="Tools"; python -m pytest Tools/tests -v
```

Expected: generator exits 0 with no stderr; `Patches/Apparel/OE_Armor.xml` and `Patches/Apparel/OE_Helmets.xml` exist; `git status` shows no changes to slice 1 generated files (`Defs/Ammo`, `Defs/RecipeDefs`, `Patches/Weapons`, `Patches/PawnKinds`); all tests pass (52 from slice 1 + 30 new = 82).

- [ ] **Step 10: Spot-check generated XML**

Run:

```powershell
rg -c "PatchOperationAddModExtension" Patches/Apparel/OE_Armor.xml Patches/Apparel/OE_Helmets.xml
rg -n "Shield|Barrier|Grenadier|Uniform|Beastmaster" Patches/Apparel
```

Expected: armor file 24 mod extensions (32 pieces minus 8 Spacer/Smoker children of catalogued concrete parents), helmets file 23 (32 minus 9 `_M_Spacer`/`_M_Melee`/`_M_Ranged` children); the second command prints nothing.

- [ ] **Step 11: Commit**

```bash
git add catalog/armor.yaml catalog/helmets.yaml Tools/oe_ce/generate.py Tools/tests/test_generate.py Tools/tests/test_apparel_coverage.py Patches/Apparel
git commit -m "feat: catalog Core armor and helmets and generate CE apparel patches"
```

---

### Task 6: In-game smoke (human)

**Files:** none

**Interfaces:**
- Consumes: the mod folder `C:\Projects\Obsidia-CE-Patch\.worktrees\feat-slice-1-core-weapons` (or the main clone after merge), loaded after Combat Extended and Obsidia Expansion Core.

- [ ] **Step 1: Start a dev-mode game. Check the log has no XML patch errors mentioning `OE_Armor.xml` / `OE_Helmets.xml`, `PartialArmorExt`, or a failed `PatchOperationConditional`.**

- [ ] **Step 2: Spawn `OCC_Armor` and `OCC_Helmet`. Info card shows sharp 20 / blunt 45 (helmet 16 / 36), heat 0.54, bulk / worn bulk, and the partial coverage on neck and arms (helmet: eyes, nose).**

- [ ] **Step 3: Put a colonist in OCC armor + helmet. CE inventory weight is not overloaded by the armor alone (carry weight +80).**

- [ ] **Step 4: Spawn `OTC_Armor` on a second colonist. Fire the same rifle at both; the OTC wearer takes noticeably more wounds.**

- [ ] **Step 5: Shoot a colonist with and without a helmet; without it, head hits wound far more.**

- [ ] **Step 6: Spawn `OCC_Armor_M_Shield` and `OES_Armor_Shield`. Both still work as Obsidia made them. The OCC one shows `OCC_Armor_M` CE ratings (inherited); the OES one stays vanilla.**

If a check fails, change the catalog, rung table or emitter tests and regenerate. Do not hand-edit generated XML.

---

## Spec coverage

| Spec item | Task |
|---|---|
| Combat armor + helmets only; excludes (uniform, shield, barrier, grenadier, Grenade_, job helmets incl. beastmaster, worker shell) | 2 (exclude rules + scan), 5 (catalog) |
| Sets with default rung + member overrides, shared set ids | 3 (model + loader), 5 (YAML) |
| Inheritance walk for layers; concrete parents | 2 |
| Child of catalogued parent: no second `PartialArmorExt`, same template | 3 (validator), 4 (emitter) |
| Separate armor rung table, OTC below OCC at both tiers, OMG above T4 | 1, 5 (catalog check) |
| CE reference points, heat scale, helmet ladder | 1 |
| Coverage templates light / marine / heavy | 1, 4 |
| Carry weight / bulk on body armor only | 1, 4 |
| Conditional replace-or-add for inherited stats | 4 |
| No new Defs; no recipes / traders / pawnKinds | 4, 5 (only `Patches/Apparel` written) |
| Generator fails on missing / duplicate / excluded / kind mismatch / template mismatch / missing Apparel dir | 3, 5 |
| Tests listed in spec | 1, 3, 4, 5 |
| Playtest bar | 6 |
| Bodies, turrets, vehicles, DLC apparel, shield comps | not tasked |
