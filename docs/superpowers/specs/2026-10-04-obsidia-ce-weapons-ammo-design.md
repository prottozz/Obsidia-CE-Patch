# Obsidia CE Patch — Slice 1: Core Weapons, Ammo, Raid Ammo

**Date:** 2026-10-04  
**Repo:** [prottozz/Obsidia-CE-Patch](https://github.com/prottozz/Obsidia-CE-Patch)  
**Status:** Draft for user review (brainstorming gate)

Standalone Combat Extended compatibility mod for **Obsidia Expansion Core** (`ObsidiaExpansion.Core`, Steam `2519492373`). This spec covers **slice 1 only**. Later specs cover armor, pawn body stats, turrets, vehicles, and DLC/mod modules.

## Goal

Core 1.6 ranged and melee weapons work under Combat Extended: CE verbs, magazines, reloads, shared family ammo, and raid pawns that spawn with the right cartridges. Faction skins of the same gun share ammo and differ only in weapon stats.

## Out of scope (slice 1)

- Apparel / armor / helmets
- Pawn race armor, health, and melee tools on animals/mechs **except** ammo for guns they already carry
- Turrets, `OE_AmmoKit` as turret fuel, artillery
- Vehicles (VVE Nightmare / MCV)
- Royalty, Ideology, Biotech, Anomaly, Odyssey, VFE Insectoids, Gravship, EBSG weapon extras
- CE `ModPatches/` PR (this is a standalone workshop-style mod)

## Dependencies

| | |
|---|---|
| RimWorld | 1.6 |
| `packageId` | `prottozz.ObsidiaCEPatch` |
| Requires | `CETeam.CombatExtended`, `ObsidiaExpansion.Core` |
| `loadAfter` | both of the above |
| Harmony | not required for slice 1 (XML only) |

## Architecture

The RimWorld mod loads only `About/`, `Defs/`, and `Patches/`.

```
Obsidia-CE-Patch/
  About/About.xml
  LoadFolders.xml
  catalog/                 # source of truth (YAML)
    ballistic.yaml
    energy.yaml
    fire.yaml
    emp.yaml
    acid.yaml
    cryo.yaml
    bio.yaml
    melee.yaml
  Tools/                   # not in LoadFolders
    generate_ce_patch.py
    validate_catalog.py
  Defs/                    # generated, committed
  Patches/                 # generated, committed
  docs/superpowers/
```

**Data flow:** catalog YAML + a read of Obsidia `1.6/Core` weapon XML → generator → committed XML. Players do not need Python. Regenerating after an Obsidia update is a Tool run, then commit.

**Failure policy:** the generator exits non-zero on catalog errors. It does not skip unknown guns.

## Ammo model

Ammo identity is **weapon type × damage class**, not faction and not tech tier.

### Type

`pistol` | `smg` | `shotgun` | `rifle` | `sniper` | `bow` | `lmg` | `minigun` | `launcher` | `rocket`

Add a type only when a Core gun does not fit the list.

### Class

| Class | Meaning |
|---|---|
| `ballistic` | Kinetic / conventional |
| `energy` | Generic charged / non-elemental energy |
| `fire` | Fire elemental |
| `emp` | Dedicated EMP weapons |
| `acid` | Acid elemental |
| `cryo` | Cryo elemental |
| `bio` | Mutated / cult / bio-weapon |

Elemental skins of the same name are **different classes**, not cartridge switches. `Quasar(Fire)` and `Quasar(EMP)` do not share an `AmmoSet`.

### Cartridges

Every ranged family has **standard**, **ap**, and **hp** (energy/bio use the same three roles: default / anti-armor / anti-flesh, named to fit the class).

**EMP extra round:** `shotgun`, `rifle`, `sniper`, `lmg`, `minigun`, and `bow` families that are **not** `class: emp` also get a fourth cartridge, `emp`. Its EMP effect is **strictly weaker** than the dedicated `class: emp` family of the **same type**. Pistol and SMG families must not have this fourth round.

Dedicated `class: emp` guns use a full EMP AmmoSet (standard / ap / hp analogue for EMP), not the weak side-cartridge.

### Sharing

Same named family across factions and tiers uses **one** AmmoSet. Example: Proto Cerberus, OCC Cerberus, Reforged Cerberus, Heroic Cerberus, Mech Cerberus all use ballistic `rifle` ammo. Only range, warmup, burst, spread, magazine, bulk, and similar gun stats change.

**Experimental** families set `experimental: true` and get a unique AmmoSet. Default is `false`. A gun is experimental only when catalogued that way (unique named one-offs, not “Prototype” as a second tier of a shared family such as Celestial Prototype).

## Catalog schema

One YAML file per class. Same schema in each.

```yaml
families:
  - id: cerberus
    type: rifle
    class: ballistic
    experimental: false
    cartridges: [standard, ap, hp, emp]  # emp because type is rifle
    members:
      - defName: OE_Rifle
        rung: proto
        range: 30.9
        warmup: 1.0
        # other overrides optional
      - defName: OCC_Rifle
        rung: occ
```

`melee.yaml` lists Core melee `defName`s and rungs. No AmmoSet. Generator emits `ToolCE` only.

### Generator invariants

Fail if:

1. A Core ranged `defName` (non-abstract, has a shoot verb) is missing from the catalog
2. Two families list the same `defName`
3. `emp` cartridge is present on `pistol` or `smg`
4. `shotgun` / `rifle` / `sniper` / `lmg` / `minigun` / `bow` and `class != emp` is missing `emp`
5. Dedicated `class: emp` EMP damage/stun is not greater than that type’s non-emp family’s `emp` cartridge

## Power rungs (balance spine)

**ODC T1–T4** is the reference scale. Weapon stats (not ammo) follow the rung.

| Rung | CE analogue |
|---|---|
| `proto` | Spacer; charge rifle neighbourhood |
| `odc_t1` | Marine kit |
| `odc_t2` | Cataphract neighbourhood |
| `odc_t3` | Below unique / persona |
| `odc_t4` | Unique / persona |
| `occ` | Marine (`odc_t1`). Standard-issue. Armor is marine; this slice only sets guns |
| `otc` | Worse armor than OCC (later spec). **Weapons better than OCC** |
| `omc` | General military; guns better than OTC |
| `oec` | Slight upgrade over OMC (bounty hunters) |
| `oe` | Empire cross-tech: above OEC, **below** `odc_t3` |
| `occ_reforge` | OCC second tier = `odc_t3` |
| `omc_mod` | OMC modified = `odc_t3` |
| `oec_t2` / `otc_t2` | Second tiers = `odc_t3` |
| `cac_t1` | Cult first tech = `odc_t3` (dark archotech) |
| `cac_t2` | Cult second tech = `odc_t4` |
| `bio_t3` / `bio_t4` | OE bioengineering two depths = `odc_t3` / `odc_t4` |
| `omg` | Most expensive Empire-elite line; **slightly above** `odc_t4` and `cac_t2` |
| `heroic` | OES Heroic = `odc_t4` / persona |
| `trophy` | Unique / persona |
| `mech` | Same family ammo as the player gun; **weapon stats** tuned for that mech, not the player tree |

`odc_t3` stays below unique/persona monsters. `odc_t4` matches them. `omg` sits slightly above.

## What the generator writes

### Defs (new)

- `CombatExtended.AmmoSetDef` per family
- `CombatExtended.AmmoDef` items per cartridge
- CE projectiles (`ProjectileCE`) per cartridge
- RecipeDefs: small and large batches, `recipeUsers` = `OE_WeaponWorkbench` only

Ammo recipes use **Obsidia materials**, not CE steel/chemfuel benches: `OE_Obsidian`, `OE_Mythril`, `OE_AmmoKit`, and `OE_Syntherius` / `OE_Mooncloth` when that class’s guns already cost them. Pattern matches CMC-style ammo bills (small + large stack sizes) on a dedicated workbench.

### Patches (Obsidia defs)

For each ranged member:

- `Verb_Shoot` → `Verb_ShootCE` with CE spread, recoil, warmup, range
- Add `CompAmmoUser` with the family `ammoSet`, magazine size from rung + overrides
- Replace vanilla projectile verbs
- `tools` → `ToolCE`

For each melee member: `ToolCE` only.

For each Core `PawnKindDef` whose `weaponTags` / equipment can roll a patched gun: CE inventory ammo for **that** `AmmoSet`, default cartridge **standard**. A member may set `ap_npc: true` so kinds that roll that gun spawn with AP instead. EMP/HP are never NPC defaults.

Traders that already use `OEGear` / `OEGearSell` (and equivalent corps tags) also stock matching AmmoSets.

## Playtest bar (slice 1)

1. Proto Cerberus: magazine, reload, CE verb, no vanilla bullet
2. OCC / Heroic / Mech Cerberus accept the **same** ammo item; guns differ in aim/range/spread
3. `Quasar(Fire)` rejects Cerberus rounds
4. Cerberus (rifle) can load the weak EMP cartridge; that hit is weaker EMP than `Quasar(EMP)`
5. A raid kind with Cerberus spawns with **standard** ammo and can fire more than one magazine
6. Obsidia weapon workbench shows ammo bills; they consume Obsidia mats, not CE generic ammo recipes

## Later slices (not this spec)

Armor/helmets to the same rung table; animal/mech bodies; turrets; vehicles; DLC and VEF module guns; optional CE ammo-bench duplicates (explicitly not wanted in slice 1).
