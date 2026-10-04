# Slice 1 Core Weapons and Ammo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a standalone 1.6 RimWorld mod that patches Obsidia Expansion Core guns and melee onto Combat Extended using catalog-driven shared AmmoSets, workbench ammo recipes, and raid magazine counts.

**Architecture:** YAML catalogs under `catalog/` are the source of truth. Python in `Tools/` reads those files plus Obsidia `1.6/Core` weapon XML and writes committed `Defs/` and `Patches/`. RimWorld never loads `Tools/` or `catalog/`. Guns are patched with `CombatExtended.PatchOperationMakeGunCECompatible`. Raid ammo uses `CombatExtended.LoadoutPropertiesExtension`.

**Tech Stack:** Python 3.11+, PyYAML, pytest, RimWorld 1.6 XML patches, Combat Extended `AmmoSetDef` / `AmmoDef` / `ProjectilePropertiesCE`.

## Global Constraints

- RimWorld 1.6 only.
- `packageId` is `prottozz.ObsidiaCEPatch`.
- Requires and `loadAfter` `CETeam.CombatExtended` and `ObsidiaExpansion.Core`.
- Harmony is not used in slice 1 (XML only).
- Ammo identity is type × class; faction skins share one AmmoSet.
- Elemental skins are different classes (`Quasar(Fire)` ≠ `Quasar(EMP)`).
- Cartridges: `standard`, `ap`, `hp`; plus `emp` on shotgun/rifle/sniper/lmg/minigun/bow when `class != emp`.
- Pistol and SMG must not have an `emp` cartridge.
- Dedicated `class: emp` EMP is strictly stronger than that type’s side-cartridge EMP.
- Ammo recipes: `recipeUsers` = `OE_WeaponWorkbench` only; materials `OE_Obsidian`, `OE_Mythril`, `OE_AmmoKit`, plus `OE_Syntherius`/`OE_Mooncloth` for classes that already cost them.
- Do not add `CE_AutoEnableCrafting_TableMachining` or `CE_AutoEnableCrafting_FabricationBench` on ammo.
- NPC default cartridge is `standard`. `ap_npc: true` on a member opts AP in. EMP/HP are never NPC defaults.
- Out of scope: armor, turret fuel, vehicles, DLC/VEF module guns.
- Obsidia source tree for scans: `C:\Projects\Assistant\294100\2519492373\1.6\Core` (override with env `OBSIDIA_CORE`).
- Generated XML is UTF-8, committed, and must be reproducible (stable sort by defName).

## File map

| Path | Responsibility |
|---|---|
| `About/About.xml` | Mod metadata, dependencies |
| `LoadFolders.xml` | Load `Defs` and `Patches` only |
| `.gitignore` | Python caches, `.superpowers/` |
| `catalog/*.yaml` | Families, members, rungs |
| `Tools/oe_ce/*.py` | Catalog load, validate, scan, emit, generate |
| `Tools/tests/` | pytest |
| `Defs/` | Generated ammo, recipes |
| `Patches/` | Generated gun, melee, pawnkind patches |

---

### Task 1: Mod skeleton

**Files:**
- Create: `About/About.xml`
- Create: `LoadFolders.xml`
- Create: `.gitignore`
- Create: `Tools/requirements.txt`
- Create: `Tools/tests/test_skeleton.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: nothing
- Produces: loadable RimWorld mod folder that does not include `Tools/` or `catalog/`

- [ ] **Step 1: Write the failing test**

```python
# Tools/tests/test_skeleton.py
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_loadfolders_does_not_load_tools_or_catalog():
    text = (ROOT / "LoadFolders.xml").read_text(encoding="utf-8")
    assert "Tools" not in text
    assert "catalog" not in text
    assert "<li>Defs</li>" in text
    assert "<li>Patches</li>" in text


def test_about_package_id():
    text = (ROOT / "About" / "About.xml").read_text(encoding="utf-8")
    assert "<packageId>prottozz.ObsidiaCEPatch</packageId>" in text
    assert "CETeam.CombatExtended" in text
    assert "ObsidiaExpansion.Core" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest Tools/tests/test_skeleton.py -v`  
Expected: FAIL because `LoadFolders.xml` does not exist.

- [ ] **Step 3: Write the skeleton files**

`About/About.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
  <name>Obsidia Expansion - Combat Extended Patch</name>
  <author>prottozz</author>
  <packageId>prottozz.ObsidiaCEPatch</packageId>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
  <modDependencies>
    <li>
      <packageId>CETeam.CombatExtended</packageId>
      <displayName>Combat Extended</displayName>
      <steamWorkshopUrl>steam://url/CommunityFilePage/2890901044</steamWorkshopUrl>
    </li>
    <li>
      <packageId>ObsidiaExpansion.Core</packageId>
      <displayName>Obsidia Expansion</displayName>
      <steamWorkshopUrl>steam://url/CommunityFilePage/2519492373</steamWorkshopUrl>
    </li>
  </modDependencies>
  <loadAfter>
    <li>CETeam.CombatExtended</li>
    <li>ObsidiaExpansion.Core</li>
  </loadAfter>
  <description>Combat Extended compatibility for Obsidia Expansion Core weapons, ammo, and raid magazines.</description>
</ModMetaData>
```

`LoadFolders.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<loadFolders>
  <v1.6>
    <li>/</li>
    <li>Defs</li>
    <li>Patches</li>
  </v1.6>
</loadFolders>
```

`.gitignore`:

```
__pycache__/
.pytest_cache/
.superpowers/
*.pyc
.venv/
```

`Tools/requirements.txt`:

```
pyyaml>=6.0
pytest>=8.0
```

Replace `README.md` with:

```markdown
# Obsidia Expansion - Combat Extended Patch

Standalone CE patch for Obsidia Expansion Core. Catalog in `catalog/`, generator in `Tools/`. RimWorld loads `Defs/` and `Patches/` only.
```

Create `Defs/.gitkeep` and `Patches/.gitkeep`.

- [ ] **Step 4: Run tests**

Run: `pip install -r Tools/requirements.txt` then `python -m pytest Tools/tests/test_skeleton.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add About/About.xml LoadFolders.xml .gitignore Tools/requirements.txt Tools/tests/test_skeleton.py README.md Defs/.gitkeep Patches/.gitkeep
git commit -m "chore: add standalone CE patch mod skeleton"
```

---

### Task 2: Catalog model and cartridge rules

**Files:**
- Create: `Tools/oe_ce/__init__.py`
- Create: `Tools/oe_ce/constants.py`
- Create: `Tools/oe_ce/models.py`
- Create: `Tools/tests/test_models.py`

**Interfaces:**
- Consumes: nothing
- Produces: `Family.resolved_cartridges() -> list[str]`; `Member`; `Catalog`

- [ ] **Step 1: Write the failing test**

```python
# Tools/tests/test_models.py
from oe_ce.models import Family, Member


def test_rifle_ballistic_gets_emp_cartridge():
    fam = Family(id="cerberus", type="rifle", class_name="ballistic", experimental=False, cartridges=None, members=[])
    assert fam.resolved_cartridges() == ["standard", "ap", "hp", "emp"]


def test_pistol_must_not_include_emp():
    fam = Family(id="impaler", type="pistol", class_name="ballistic", experimental=False, cartridges=None, members=[])
    assert fam.resolved_cartridges() == ["standard", "ap", "hp"]


def test_emp_class_rifle_has_no_side_emp_cartridge():
    fam = Family(id="quasar", type="rifle", class_name="emp", experimental=False, cartridges=None, members=[])
    assert fam.resolved_cartridges() == ["standard", "ap", "hp"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd C:\Projects\Obsidia-CE-Patch
$env:PYTHONPATH="Tools"
python -m pytest Tools/tests/test_models.py -v
```

Expected: FAIL `ModuleNotFoundError: No module named 'oe_ce'`

- [ ] **Step 3: Implement constants and models**

`Tools/oe_ce/__init__.py` empty.

`Tools/oe_ce/constants.py`:

```python
WEAPON_TYPES = (
    "pistol", "smg", "shotgun", "rifle", "sniper",
    "bow", "lmg", "minigun", "launcher", "rocket",
)
DAMAGE_CLASSES = (
    "ballistic", "energy", "fire", "emp", "acid", "cryo", "bio",
)
EMP_SIDE_TYPES = frozenset(
    ("shotgun", "rifle", "sniper", "lmg", "minigun", "bow")
)
BASE_CARTRIDGES = ("standard", "ap", "hp")
RUNGS = (
    "proto", "odc_t1", "odc_t2", "odc_t3", "odc_t4",
    "occ", "otc", "omc", "oec", "oe",
    "occ_reforge", "omc_mod", "oec_t2", "otc_t2",
    "cac_t1", "cac_t2", "bio_t3", "bio_t4",
    "omg", "heroic", "trophy", "mech",
)
YAML_CLASS_FILES = {
    "ballistic": "ballistic.yaml",
    "energy": "energy.yaml",
    "fire": "fire.yaml",
    "emp": "emp.yaml",
    "acid": "acid.yaml",
    "cryo": "cryo.yaml",
    "bio": "bio.yaml",
}
```

`Tools/oe_ce/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field

from oe_ce.constants import BASE_CARTRIDGES, EMP_SIDE_TYPES


@dataclass
class Member:
    def_name: str
    rung: str
    range: float | None = None
    warmup: float | None = None
    burst: int | None = None
    magazine: int | None = None
    spread: float | None = None
    mass: float | None = None
    bulk: float | None = None
    ap_npc: bool = False


@dataclass
class Family:
    id: str
    type: str
    class_name: str
    experimental: bool = False
    cartridges: list[str] | None = None
    members: list[Member] = field(default_factory=list)

    def resolved_cartridges(self) -> list[str]:
        if self.cartridges is not None:
            return list(self.cartridges)
        out = list(BASE_CARTRIDGES)
        if self.class_name != "emp" and self.type in EMP_SIDE_TYPES:
            out.append("emp")
        return out

    def ammo_set_def(self) -> str:
        return f"AmmoSet_OE_{self.id}_{self.class_name}"

    def ammo_def(self, cartridge: str) -> str:
        return f"Ammo_OE_{self.id}_{self.class_name}_{cartridge}"

    def bullet_def(self, cartridge: str) -> str:
        return f"Bullet_OE_{self.id}_{self.class_name}_{cartridge}"


@dataclass
class Catalog:
    families: list[Family] = field(default_factory=list)
    melee: list[Member] = field(default_factory=list)

    def ranged_def_names(self) -> set[str]:
        names: set[str] = set()
        for fam in self.families:
            for m in fam.members:
                names.add(m.def_name)
        return names
```

YAML field `class` maps to `class_name` in Python.

- [ ] **Step 4: Run tests**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_models.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Tools/oe_ce Tools/tests/test_models.py
git commit -m "feat: add catalog family model and cartridge rules"
```

---

### Task 3: YAML load and spec validators

**Files:**
- Create: `Tools/oe_ce/load.py`
- Create: `Tools/oe_ce/validate.py`
- Create: `Tools/tests/test_validate.py`

**Interfaces:**
- Consumes: `Family.resolved_cartridges`, `Catalog`
- Produces: `load_catalog(catalog_dir: Path) -> Catalog`; `validate_catalog(catalog: Catalog, core_ranged: set[str]) -> list[str]` (empty list means OK)

- [ ] **Step 1: Write the failing test**

```python
# Tools/tests/test_validate.py
from pathlib import Path

from oe_ce.load import load_catalog
from oe_ce.models import Catalog, Family, Member
from oe_ce.validate import validate_catalog


def test_duplicate_defname_is_error():
    cat = Catalog(families=[
        Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")]),
        Family("other", "rifle", "ballistic", members=[Member("OE_Rifle", "occ")]),
    ])
    errs = validate_catalog(cat, core_ranged={"OE_Rifle"})
    assert any("OE_Rifle" in e and "duplicate" in e.lower() for e in errs)


def test_missing_core_gun_is_error():
    cat = Catalog(families=[
        Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")]),
    ])
    errs = validate_catalog(cat, core_ranged={"OE_Rifle", "OCC_Rifle"})
    assert any("OCC_Rifle" in e for e in errs)


def test_pistol_explicit_emp_is_error():
    cat = Catalog(families=[
        Family("impaler", "pistol", "ballistic", cartridges=["standard", "ap", "hp", "emp"],
               members=[Member("OE_Pistol", "proto")]),
    ])
    errs = validate_catalog(cat, core_ranged={"OE_Pistol"})
    assert any("emp" in e.lower() and "pistol" in e.lower() for e in errs)


def test_rifle_missing_emp_is_error():
    cat = Catalog(families=[
        Family("cerberus", "rifle", "ballistic", cartridges=["standard", "ap", "hp"],
               members=[Member("OE_Rifle", "proto")]),
    ])
    errs = validate_catalog(cat, core_ranged={"OE_Rifle"})
    assert any("emp" in e.lower() for e in errs)


def test_load_yaml_class_field(tmp_path: Path):
    (tmp_path / "ballistic.yaml").write_text(
        "families:\n"
        "  - id: cerberus\n"
        "    type: rifle\n"
        "    class: ballistic\n"
        "    members:\n"
        "      - defName: OE_Rifle\n"
        "        rung: proto\n",
        encoding="utf-8",
    )
    cat = load_catalog(tmp_path)
    assert cat.families[0].class_name == "ballistic"
    assert cat.families[0].members[0].def_name == "OE_Rifle"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_validate.py -v`  
Expected: FAIL import `oe_ce.validate`

- [ ] **Step 3: Implement load and validate**

`Tools/oe_ce/load.py`:

```python
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
```

`Tools/oe_ce/validate.py`:

```python
from __future__ import annotations

from collections import Counter

from oe_ce.constants import DAMAGE_CLASSES, EMP_SIDE_TYPES, RUNGS, WEAPON_TYPES
from oe_ce.models import Catalog


def validate_catalog(catalog: Catalog, core_ranged: set[str]) -> list[str]:
    errors: list[str] = []
    seen: list[str] = []
    for fam in catalog.families:
        if fam.type not in WEAPON_TYPES:
            errors.append(f"{fam.id}: unknown type {fam.type}")
        if fam.class_name not in DAMAGE_CLASSES:
            errors.append(f"{fam.id}: unknown class {fam.class_name}")
        carts = fam.resolved_cartridges()
        if fam.type in ("pistol", "smg") and "emp" in carts:
            errors.append(f"{fam.id}: pistol/smg must not have emp cartridge")
        if fam.class_name != "emp" and fam.type in EMP_SIDE_TYPES and "emp" not in carts:
            errors.append(f"{fam.id}: {fam.type} {fam.class_name} missing emp cartridge")
        for m in fam.members:
            seen.append(m.def_name)
            if m.rung not in RUNGS:
                errors.append(f"{m.def_name}: unknown rung {m.rung}")
    counts = Counter(seen)
    for name, n in counts.items():
        if n > 1:
            errors.append(f"duplicate defName {name}")
    catalogued = set(seen)
    for missing in sorted(core_ranged - catalogued):
        errors.append(f"Core ranged defName not in catalog: {missing}")
    return errors
```

- [ ] **Step 4: Run tests**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_validate.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Tools/oe_ce/load.py Tools/oe_ce/validate.py Tools/tests/test_validate.py
git commit -m "feat: load catalog YAML and enforce ammo invariants"
```

---

### Task 4: Scan Obsidia Core ranged and melee defNames

**Files:**
- Create: `Tools/oe_ce/scan_obsidia.py`
- Create: `Tools/validate_catalog.py`
- Create: `Tools/tests/test_scan.py`

**Interfaces:**
- Consumes: folder `1.6/Core`
- Produces: `scan_core_ranged(core: Path) -> set[str]`; `scan_core_melee(core: Path) -> set[str]`; `weapon_tags(core: Path, def_name: str) -> list[str]`

A ranged def is a non-abstract `ThingDef` under `Defs/ThingDefs_Misc/Weapons/` that has a `./verbs` child and `./defName`.

- [ ] **Step 1: Write the failing test**

```python
# Tools/tests/test_scan.py
from pathlib import Path

from oe_ce.scan_obsidia import scan_core_ranged

CORE = Path(r"C:\Projects\Assistant\294100\2519492373\1.6\Core")


def test_scan_finds_proto_cerberus():
    names = scan_core_ranged(CORE)
    assert "OE_Rifle" in names
    assert "OCC_Rifle" in names
    assert "Bullet_OE_R" not in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_scan.py -v`  
Expected: FAIL import.

- [ ] **Step 3: Implement the scanner**

```python
# Tools/oe_ce/scan_obsidia.py
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


def _iter_weapon_xml(core: Path) -> list[Path]:
    root = core / "Defs" / "ThingDefs_Misc" / "Weapons"
    return sorted(root.rglob("*.xml"))


def _thingdefs(path: Path) -> list[ET.Element]:
    tree = ET.parse(path)
    return list(tree.getroot())


def scan_core_ranged(core: Path) -> set[str]:
    names: set[str] = set()
    for path in _iter_weapon_xml(core):
        for el in _thingdefs(path):
            if el.tag != "ThingDef":
                continue
            if el.get("Abstract") == "True":
                continue
            def_el = el.find("defName")
            if def_el is None or not def_el.text:
                continue
            if el.find("verbs") is None:
                continue
            names.add(def_el.text.strip())
    return names


def scan_core_melee(core: Path) -> set[str]:
    names: set[str] = set()
    for path in _iter_weapon_xml(core):
        for el in _thingdefs(path):
            if el.tag != "ThingDef" or el.get("Abstract") == "True":
                continue
            def_el = el.find("defName")
            if def_el is None or not def_el.text:
                continue
            if el.find("verbs") is not None:
                continue
            if el.find("tools") is None:
                continue
            names.add(def_el.text.strip())
    return names


def weapon_tags(core: Path, def_name: str) -> list[str]:
    for path in _iter_weapon_xml(core):
        for el in _thingdefs(path):
            def_el = el.find("defName")
            if def_el is None or (def_el.text or "").strip() != def_name:
                continue
            tags = el.find("weaponTags")
            if tags is None:
                return []
            return [(li.text or "").strip() for li in tags.findall("li") if li.text]
    return []
```

`Tools/validate_catalog.py`:

```python
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from oe_ce.load import load_catalog
from oe_ce.scan_obsidia import scan_core_ranged
from oe_ce.validate import validate_catalog


def main() -> int:
    core = Path(os.environ.get("OBSIDIA_CORE", r"C:\Projects\Assistant\294100\2519492373\1.6\Core"))
    cat = load_catalog(ROOT / "catalog")
    errs = validate_catalog(cat, scan_core_ranged(core))
    for e in errs:
        print(e)
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests**

Run: `$env:PYTHONPATH="Tools"; python -m pytest Tools/tests/test_scan.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Tools/oe_ce/scan_obsidia.py Tools/validate_catalog.py Tools/tests/test_scan.py
git commit -m "feat: scan Obsidia Core weapon defNames for catalog coverage"
```

---

### Task 5: Rung default gun stats

**Files:**
- Create: `Tools/oe_ce/rungs.py`
- Create: `Tools/tests/test_rungs.py`

**Interfaces:**
- Consumes: `Member.rung`, `Family.type`
- Produces: `gun_stats(weapon_type: str, member: Member) -> dict` with keys `range`, `warmup`, `magazine`, `reload`, `spread`, `sway`, `recoil`, `cooldown`, `burst`, `mass`, `bulk`. Member overrides win.

Rifle proto matches CE charge rifle neighbourhood: range 55, warmup 1.0, mag 25, spread 0.08, recoil 1.46. OCC/odc_t1 weaker (range 48). odc_t4 range 75. omg range 78. Type range multipliers: pistol 0.55, smg 0.65, shotgun 0.40, rifle 1.0, sniper 1.25, bow 0.90, lmg 0.95, minigun 0.70, launcher 0.80, rocket 1.10. Type magazines: pistol 12, smg 25, shotgun 8, rifle 25, sniper 8, bow 1, lmg 50, minigun 80, launcher 6, rocket 1. Mech magazine `max(type, 40)`.

- [ ] **Step 1: Write the failing test**

```python
from oe_ce.models import Member
from oe_ce.rungs import gun_stats


def test_proto_rifle_matches_charge_rifle_neighbourhood():
    s = gun_stats("rifle", Member("OE_Rifle", "proto"))
    assert s["range"] == 55
    assert s["warmup"] == 1.0
    assert s["magazine"] == 25


def test_occ_weaker_than_proto():
    proto = gun_stats("rifle", Member("OE_Rifle", "proto"))
    occ = gun_stats("rifle", Member("OCC_Rifle", "occ"))
    assert occ["range"] < proto["range"]


def test_omg_above_odc_t4():
    t4 = gun_stats("rifle", Member("X", "odc_t4"))
    omg = gun_stats("rifle", Member("Y", "omg"))
    assert omg["range"] > t4["range"]


def test_member_override_wins():
    s = gun_stats("rifle", Member("OE_Rifle", "proto", range=40.0))
    assert s["range"] == 40.0
```

- [ ] **Step 2: Run test to verify it fails**  
Expected: FAIL import `oe_ce.rungs`

- [ ] **Step 3: Implement `rungs.py`**

Define `RIFLE_BY_RUNG` for every name in `RUNGS`. `occ` copies `odc_t1`. `occ_reforge`, `omc_mod`, `oec_t2`, `otc_t2`, `cac_t1`, `bio_t3` copy `odc_t3`. `cac_t2`, `bio_t4`, `heroic`, `trophy` copy `odc_t4`. `mech` copies `omc` then magazine bump. `otc` between occ and omc (range 50). `omc` 52, `oec` 53, `oe` 54, `odc_t2` 62.

```python
def gun_stats(weapon_type: str, member: Member) -> dict:
    row = dict(RIFLE_BY_RUNG[member.rung])
    row["range"] = round(row["range"] * TYPE_RANGE_MULT[weapon_type], 2)
    row["magazine"] = TYPE_MAG[weapon_type]
    if member.rung == "mech":
        row["magazine"] = max(row["magazine"], 40)
    mapping = {
        "range": member.range,
        "warmup": member.warmup,
        "burst": member.burst,
        "magazine": member.magazine,
        "spread": member.spread,
        "mass": member.mass,
        "bulk": member.bulk,
    }
    for key, val in mapping.items():
        if val is not None:
            row[key] = val
    return row
```

Include `reload` 4.0 default, bow `reload` 3.5.

- [ ] **Step 4: Run tests**  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Tools/oe_ce/rungs.py Tools/tests/test_rungs.py
git commit -m "feat: map power rungs to CE gun stat defaults"
```

---

### Task 6: Emit ammo XML

**Files:**
- Create: `Tools/oe_ce/emit_ammo.py`
- Create: `Tools/tests/test_emit_ammo.py`

**Interfaces:**
- Consumes: `Family.resolved_cartridges()`, `ammo_set_def()`, `ammo_def()`, `bullet_def()`
- Produces: `emit_ammo_xml(families: list[Family]) -> str`; module constants `EMP_SIDE_AMOUNT = 6`, `EMP_DEDICATED_AMOUNT = 18`

Ballistic rifle standard: damage 13, sharp 18, blunt 26. ap: 10 / 32. hp: 16 / 10. Side emp: damage 8, sharp 12, secondary EMP 6, `empShieldBreakChance` 0.15. Dedicated emp class standard: secondary EMP 18, shield 0.45. Parent ammo `SpacerSmallAmmoBase`, bullet `BaseBulletCE`. Graphics `Things/Ammo/Charged/MediumRegular`. ammoClass: FMJ / ArmorPiercing / HollowPoint / Ionized. No CE auto-craft tags. Sort families by `(class_name, id)`.

- [ ] **Step 1: Write the failing test**

```python
from oe_ce.emit_ammo import EMP_DEDICATED_AMOUNT, EMP_SIDE_AMOUNT, emit_ammo_xml
from oe_ce.models import Family, Member


def test_cerberus_set_and_emp_weaker_than_dedicated():
    cerb = Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")])
    quasar = Family("quasar", "rifle", "emp", members=[Member("OTC_Rifle_EMP", "otc")])
    xml = emit_ammo_xml([cerb, quasar])
    assert "AmmoSet_OE_cerberus_ballistic" in xml
    assert "Ammo_OE_cerberus_ballistic_emp" in xml
    assert "Ammo_OE_cerberus_ballistic_standard" in xml
    assert EMP_DEDICATED_AMOUNT > EMP_SIDE_AMOUNT
    assert f"<amount>{EMP_SIDE_AMOUNT}</amount>" in xml
    assert f"<amount>{EMP_DEDICATED_AMOUNT}</amount>" in xml
    assert "CE_AutoEnableCrafting_TableMachining" not in xml
```

- [ ] **Step 2: Run test to verify it fails**  
Expected: FAIL import

- [ ] **Step 3: Implement `emit_ammo.py`** emitting `ThingCategoryDef`, `CombatExtended.AmmoSetDef`, `AmmoDef` items, and `ProjectilePropertiesCE` bullets. Standard cartridge is first in `ammoTypes`. Side emp uses `EMP_SIDE_AMOUNT`; `class_name == "emp"` uses `EMP_DEDICATED_AMOUNT`.

- [ ] **Step 4: Run tests**  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Tools/oe_ce/emit_ammo.py Tools/tests/test_emit_ammo.py
git commit -m "feat: generate CE AmmoSets and projectiles from families"
```

---

### Task 7: Emit workbench ammo recipes

**Files:**
- Create: `Tools/oe_ce/emit_recipes.py`
- Create: `Tools/tests/test_emit_recipes.py`

**Interfaces:**
- Consumes: `Family.ammo_def`
- Produces: `emit_recipe_xml(families: list[Family]) -> str`

Two recipes per ammo def: `MakeAmmo_OE_{id}_{class}_{cartridge}_small` (×200) and `_large` (×500). `recipeUsers` only `OE_WeaponWorkbench`. Ballistic ingredients small: Obsidian 8, Mythril 4, AmmoKit 2; large ×4. Energy/fire/acid/cryo/emp/bio add Syntherius 2/8. Fire/bio add Mooncloth 1/4.

- [ ] **Step 1: Write the failing test**

```python
from oe_ce.emit_recipes import emit_recipe_xml
from oe_ce.models import Family, Member


def test_recipes_use_obsidia_bench_and_mats():
    fam = Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")])
    xml = emit_recipe_xml([fam])
    assert "OE_WeaponWorkbench" in xml
    assert "OE_Obsidian" in xml
    assert "OE_AmmoKit" in xml
    assert "TableMachining" not in xml
    assert "MakeAmmo_OE_cerberus_ballistic_standard_small" in xml
    assert "MakeAmmo_OE_cerberus_ballistic_standard_large" in xml
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement `emit_recipes.py`**

- [ ] **Step 4: Run tests**  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Tools/oe_ce/emit_recipes.py Tools/tests/test_emit_recipes.py
git commit -m "feat: craft Obsidia CE ammo on the weapon workbench"
```

---

### Task 8: Emit gun patches

**Files:**
- Create: `Tools/oe_ce/emit_guns.py`
- Create: `Tools/tests/test_emit_guns.py`

**Interfaces:**
- Consumes: `Family`, `Member`, `gun_stats()`, ammo def names
- Produces: `emit_gun_patches(families: list[Family]) -> str`

Each member is one `CombatExtended.PatchOperationMakeGunCECompatible`. `defaultProjectile` is the family's **standard** bullet. `AmmoUser.ammoSet` is the family set. Magazine/reload/range/warmup/spread from `gun_stats`. Also replace `tools` with two `CombatExtended.ToolCE` nodes (stock blunt power 6, barrel poke power 6). Sort members by `def_name`.

- [ ] **Step 1: Write the failing test**

```python
from oe_ce.emit_guns import emit_gun_patches
from oe_ce.models import Family, Member


def test_shared_ammoset_different_stats():
    fam = Family(
        "cerberus",
        "rifle",
        "ballistic",
        members=[
            Member("OE_Rifle", "proto"),
            Member("OCC_Rifle", "occ"),
        ],
    )
    xml = emit_gun_patches([fam])
    assert xml.count("AmmoSet_OE_cerberus_ballistic") == 2
    assert "<defName>OE_Rifle</defName>" in xml
    assert "<defName>OCC_Rifle</defName>" in xml
    assert "PatchOperationMakeGunCECompatible" in xml
    assert "<range>55</range>" in xml
    assert "<range>48</range>" in xml
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement `emit_guns.py`**

- [ ] **Step 4: Run tests**  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Tools/oe_ce/emit_guns.py Tools/tests/test_emit_guns.py
git commit -m "feat: emit CE MakeGun patches sharing family ammo"
```

---

### Task 9: Melee ToolCE and pawnKind loadouts

**Files:**
- Create: `Tools/oe_ce/emit_melee.py`
- Create: `Tools/oe_ce/emit_pawnkinds.py`
- Create: `Tools/tests/test_emit_melee_pawnkinds.py`

**Interfaces:**
- Consumes: `Catalog.melee`, `weapon_tags()`, Core `Defs/PawnKinds`
- Produces: `emit_melee_xml(members: list[Member]) -> str`; `emit_pawnkind_xml(core: Path, families: list[Family]) -> str`

Melee: `PatchOperationReplace` xpath `Defs/ThingDef[defName="{def}"]/tools` with ToolCE handle+blade (CE knife layout), power proto 8 / odc_t3 14 / omg 18.

PawnKinds: for each `PawnKindDef` whose `weaponTags` intersect a catalogued gun's tags, add `CombatExtended.LoadoutPropertiesExtension` with `primaryMagazineCount` min 4 max 8. AmmoTypes already list standard first, so NPCs get standard. Do not emit a `preferredAmmo` field (CE loadout extension uses magazine counts, not a preferred ammo def). `ap_npc: true` increases `primaryMagazineCount` min/max to 6/12 only; still standard cartridge.

- [ ] **Step 1: Write tests** that `weapon_tags(CORE, "OE_Rifle")` contains `OESniperGun`, melee XML contains `CombatExtended.ToolCE`, and pawnkind XML contains `LoadoutPropertiesExtension` and `OCC_Recruit` after cataloguing `OCC_Rifle`.

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Implement emitters**

- [ ] **Step 4: Run tests**  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Tools/oe_ce/emit_melee.py Tools/oe_ce/emit_pawnkinds.py Tools/tests/test_emit_melee_pawnkinds.py
git commit -m "feat: patch melee tools and raid magazine counts"
```

---

### Task 10: Generator CLI and Cerberus catalog

**Files:**
- Create: `Tools/oe_ce/generate.py`
- Create: `Tools/generate_ce_patch.py`
- Create: `Tools/tests/test_generate.py`
- Create: `catalog/ballistic.yaml`
- Create: `catalog/energy.yaml`
- Create: `catalog/fire.yaml`
- Create: `catalog/emp.yaml`
- Create: `catalog/acid.yaml`
- Create: `catalog/cryo.yaml`
- Create: `catalog/bio.yaml`
- Create: `catalog/melee.yaml`

**Interfaces:**
- Consumes: all emitters, `load_catalog`, `validate_catalog`, `scan_core_ranged`
- Produces: `generate(root: Path) -> None` writing `Defs/Ammo/OE_Ammo.xml`, `Defs/RecipeDefs/OE_AmmoRecipes.xml`, `Patches/Weapons/OE_Ranged.xml`, `Patches/Weapons/OE_Melee.xml`, `Patches/PawnKinds/OE_Loadouts.xml`

`generate` calls `validate_catalog` and exits 1 if errors unless `OE_CE_ALLOW_PARTIAL=1`.

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path
from oe_ce.generate import generate

ROOT = Path(__file__).resolve().parents[2]


def test_generate_cerberus_files(monkeypatch):
    monkeypatch.setenv("OE_CE_ALLOW_PARTIAL", "1")
    generate(ROOT)
    ammo = (ROOT / "Defs" / "Ammo" / "OE_Ammo.xml").read_text(encoding="utf-8")
    guns = (ROOT / "Patches" / "Weapons" / "OE_Ranged.xml").read_text(encoding="utf-8")
    assert "AmmoSet_OE_cerberus_ballistic" in ammo
    assert "OE_Rifle" in guns
    assert "OCC_Rifle" in guns
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Grep Core weapons for `Cerberus` and put every matching gun `defName` in `catalog/ballistic.yaml` family `id: cerberus`, `type: rifle`, rungs proto/occ/occ_reforge/heroic/mech as labeled. Empty `families: []` in other class files. `melee.yaml` `members: []`. Implement `generate.py` and `generate_ce_patch.py`.

- [ ] **Step 4: Run tests**  
Expected: PASS with `OE_CE_ALLOW_PARTIAL=1`

- [ ] **Step 5: Commit**

```bash
git add catalog Tools/oe_ce/generate.py Tools/generate_ce_patch.py Tools/tests/test_generate.py Defs Patches
git commit -m "feat: generate committed CE XML for Cerberus family"
```

---

### Task 11: EMP constant check and ammo trade tags

**Files:**
- Modify: `Tools/oe_ce/validate.py`
- Modify: `Tools/oe_ce/emit_ammo.py`
- Create: `Tools/tests/test_emp_and_trade.py`

**Interfaces:**
- Consumes: `EMP_SIDE_AMOUNT`, `EMP_DEDICATED_AMOUNT`
- Produces: `validate_emp_constants() -> list[str]`; ammo `tradeTags` `CE_AutoEnableTrade` and `OEGear` only (no CE auto-craft tags)

- [ ] **Step 1: Write tests**

```python
from oe_ce.emit_ammo import EMP_DEDICATED_AMOUNT, EMP_SIDE_AMOUNT, emit_ammo_xml
from oe_ce.models import Family, Member
from oe_ce.validate import validate_emp_constants


def test_emp_constants():
    assert validate_emp_constants() == []
    assert EMP_DEDICATED_AMOUNT > EMP_SIDE_AMOUNT


def test_ammo_trade_tags():
    xml = emit_ammo_xml([Family("cerberus", "rifle", "ballistic", members=[Member("OE_Rifle", "proto")])])
    assert "CE_AutoEnableTrade" in xml
    assert "OEGear" in xml
    assert "CE_AutoEnableCrafting_TableMachining" not in xml
```

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Add `validate_emp_constants` and call it from `validate_catalog`. Add the two trade tags on each `AmmoDef`.

- [ ] **Step 4: Run tests**  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Tools/oe_ce/validate.py Tools/oe_ce/emit_ammo.py Tools/tests/test_emp_and_trade.py
git commit -m "feat: enforce EMP strength gap and Obsidia ammo trade tags"
```

---

### Task 12: Full Core catalog coverage

**Files:**
- Modify: `catalog/*.yaml`
- Create: `Tools/tests/test_coverage.py`

**Interfaces:**
- Consumes: `scan_core_ranged`, `load_catalog`, `validate_catalog`
- Produces: `validate_catalog` returns `[]` with `OE_CE_ALLOW_PARTIAL` unset

- [ ] **Step 1: Write the failing test**

```python
import os
from pathlib import Path
from oe_ce.load import load_catalog
from oe_ce.scan_obsidia import scan_core_ranged
from oe_ce.validate import validate_catalog

ROOT = Path(__file__).resolve().parents[2]
CORE = Path(os.environ.get("OBSIDIA_CORE", r"C:\Projects\Assistant\294100\2519492373\1.6\Core"))


def test_core_ranged_fully_catalogued():
    cat = load_catalog(ROOT / "catalog")
    errs = validate_catalog(cat, scan_core_ranged(CORE))
    assert errs == [], "\n".join(errs)
```

- [ ] **Step 2: Run test to verify it fails** with missing defNames printed

- [ ] **Step 3: Put every missing defName into the correct class YAML.** Shared label stem across factions = one `id`. `(Fire)`/`(EMP)`/`(Acid)`/`(Cryo)` go in that class file with the same `type` as the ballistic twin. Trophy/Heroic/Mech members use rungs `trophy`/`heroic`/`mech`. Unique names with no twin: `experimental: true` and their own `id`. Melee-only defs go in `melee.yaml`. Then:

```bash
$env:PYTHONPATH="Tools"
Remove-Item Env:OE_CE_ALLOW_PARTIAL -ErrorAction SilentlyContinue
python Tools/generate_ce_patch.py
python -m pytest Tools/tests -v
```

- [ ] **Step 4: Run coverage test**  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add catalog Defs Patches Tools/tests/test_coverage.py
git commit -m "feat: catalog all Obsidia Core weapons for CE ammo sharing"
```

---

### Task 13: In-game smoke

**Files:** none

**Interfaces:**
- Consumes: generated mod at `C:\Projects\Obsidia-CE-Patch`

- [ ] **Step 1: Add `C:\Projects\Obsidia-CE-Patch` as a local mod in RimSort. Enable after CE and Obsidia.**

- [ ] **Step 2: Dev-mode spawn `OE_Rifle`. Confirm magazine, reload, CE verb, no vanilla bullet.**

- [ ] **Step 3: Spawn OCC and Mech Cerberus. Confirm they accept `Ammo_OE_cerberus_ballistic_standard`.**

- [ ] **Step 4: Confirm a Fire Quasar rejects Cerberus ammo.**

- [ ] **Step 5: Load Cerberus EMP cartridge; EMP weaker than dedicated EMP Quasar.**

- [ ] **Step 6: Force-spawn an OCC kind with a Cerberus-capable tag; they fire more than one magazine.**

- [ ] **Step 7: Obsidia weapon workbench shows ammo bills using Obsidian/Mythril/AmmoKit.**

If a check fails, change catalog or emitter tests and regenerate. Do not hand-edit generated XML.

---

## Spec coverage

| Spec item | Task |
|---|---|
| Standalone packageId / loadAfter | 1 |
| Catalog YAML per class | 3, 10, 12 |
| Type × class ammo, shared skins | 2, 8, 10 |
| EMP side cartridge vs dedicated | 2, 6, 11 |
| Pistol/SMG no EMP | 2, 3 |
| Generator fails on missing/duplicate | 3, 4, 12 |
| Rungs / proto charge-rifle / OMG above T4 | 5 |
| MakeGun + ammo user | 8 |
| ToolCE melee | 9 |
| Raid standard magazines | 9 |
| Workbench recipes, Obsidia mats | 7 |
| OEGear trade | 11 |
| Playtest bar | 13 |
| Armor/turrets/DLC | not tasked |
| `ap_npc` | 9 (more mags, still standard first) |
| Experimental unique AmmoSet | 12 (`experimental: true` + unique `id`) |
