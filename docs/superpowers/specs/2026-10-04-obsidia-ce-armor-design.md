# Obsidia CE Patch — Slice 2: Core Armor and Helmets

**Date:** 2026-10-04  
**Repo:** [prottozz/Obsidia-CE-Patch](https://github.com/prottozz/Obsidia-CE-Patch)  
**Status:** Draft for user review (brainstorming gate)

Standalone Combat Extended compatibility for **Obsidia Expansion Core** combat body armor and helmets. Slice 1 already patched Core guns, melee, ammo, and raid magazines. This spec does not change those.

## Goal

Core 1.6 combat armor and helmets use Combat Extended sharp / blunt / heat ratings, bulk, and `PartialArmor` coverage so colonists and raiders are neither vanilla sponges nor paper. Pieces are grouped into named sets (OCC kit, ODC Recon, …) and balanced from a **separate armor rung table** that reuses the slice 1 rung *names*.

## Out of scope

- Uniforms and other non-armor clothing (`OE_Uniform_*`)
- Shield and barrier apparel (`*Shield`, `*Barrier`)
- Grenadier kits and grenade projectile defs living in Apparel XML (`*Grenadier*`, `Grenade_*`)
- Job / utility helmets (miner, medic, constructor, trader, worker exohelm)
- Pawn race bodies, animal/mech health
- Turrets, vehicles
- Royalty / Ideology / Biotech / Anomaly / Odyssey / VFE / Gravship / EBSG apparel
- New ammo, gun, or melee patches
- CE machining-bench armor recipes (Obsidia armor stays on `OE_ArmorStation`)

## Dependencies

Unchanged from slice 1: RimWorld 1.6, `prottozz.ObsidiaCEPatch`, requires `CETeam.CombatExtended` and `ObsidiaExpansion.Core`, `loadAfter` both. Harmony is not required (XML only).

## Architecture

RimWorld still loads only `About/`, `Defs/`, and `Patches/`. Catalog and `Tools/` stay generator-only.

**Data flow:** `catalog/armor.yaml` + `catalog/helmets.yaml` + a read of Obsidia `1.6/Core` Apparel XML → generator → committed `Patches/Apparel/`. Players do not need Python. Do not hand-edit generated XML.

**Failure policy:** generator exits non-zero if an in-scope Core piece is missing from the catalog, if two entries share a `defName`, or if a catalogued `defName` is on the exclude list.

## Catalog

Sets are the armor equivalent of gun families. They do **not** share an item the way guns share ammo; they exist so a kit (body + helm, plus `_M` / `_Spacer` / melee-ranged helm variants) stays on one rung unless a member overrides it.

```yaml
# catalog/armor.yaml
sets:
  - id: occ
    rung: occ
    members:
      - defName: OCC_Armor
      - defName: OCC_Armor_M
        rung: occ_reforge
```

```yaml
# catalog/helmets.yaml
sets:
  - id: occ
    rung: occ
    members:
      - defName: OCC_Helmet
      - defName: OCC_Helmet_M
        rung: occ_reforge
      - defName: OCC_Helmet_M_Melee
      - defName: OCC_Helmet_M_Ranged
```

Rules:

- `id` is a kit name (`occ`, `odc_recon`, `odc_duelist`, …), not a faction prefix dump.
- Matching armor and helmets use the **same set id**.
- Default `rung` is required on the set. A member may override `rung`.
- Rung names are the slice 1 list (`proto`, `occ`, `otc`, `odc_t1` … `omg`, `heroic`, `trophy`, `mech`). `mech` is unused unless Core actually has a worn combat suit for that pawn.

## Scanner and excludes

Scan `Defs/ThingDefs_Misc/Apparel` for non-abstract `ThingDef`s. Walk `ParentName` so inherited `thingClass`, apparel layers, and body groups count: Core pieces often omit those on the child def.

Treat as **in-scope combat armor** if the def uses a torso shell layer (Obsidia `OEArmorBase` / equivalent) and is not excluded.

Treat as **in-scope combat helmet** if the def uses an overhead / helmet layer and is not excluded.

**Exclude** (never catalog, never patch):

- `OE_Uniform_Military`, `OE_Uniform_Worker`
- defNames containing `Shield` or `Barrier`
- defNames containing `Grenadier`
- defNames starting with `Grenade_`
- job / worker gear: miner, medic, constructor, trader, beastmaster, worker helmets and worker shells (`ODC_Helmet_Miner`, `ODC_Helmet_Constructor`, `ODC_Helmet_Medic`, `ODC_Helmet_Trader`, `ODC_Helmet_Beastmaster`, `EGO_Helmet_Exohelm_Worker`, `EGO_Armor_Shell_Worker`, and any later Core def that is clearly the same role)

Stalker / trophy / EGO melee-ranged combat shells **are** in scope. `*_Smoker` and `*_Spacer` variants are in scope (same armor, extra ability or vacuum sealing).

**Inheritance:** Core uses concrete parents (`OCC_Armor_M_Spacer` inherits from `OCC_Armor_M`). Patches apply before XML inheritance, so:

- Shield / barrier / grenadier children of a catalogued piece inherit its CE stats and coverage even though they are never patched directly. Standalone ones with no catalogued parent (`OES_Armor_Shield`, `OES_Armor_Barrier`) stay vanilla.
- A catalogued child of a catalogued concrete parent does not get its own `PartialArmorExt` (it would duplicate the inherited one). It must resolve to the same coverage template as its parent; the validator fails otherwise.

## Armor rungs (not the gun table)

Same names as guns. **Different numbers.** `gun_stats()` must not be reused.

Confirmed ranking vs CE analogues:

| Rung | Armor analogue |
|---|---|
| `proto` | Spacer / recon flak |
| `otc` | **Strictly below** `occ` (weaker than marine). OTC guns stay stronger than OCC from slice 1; OTC armor does not. |
| `occ`, `odc_t1` | Marine |
| `omc` | About OCC (general military), not OTC |
| `oec` | Slight step above OMC |
| `oe` | Above OEC, below `odc_t3` |
| `odc_t2` | Cataphract neighbourhood |
| `otc_t2` | Same as `odc_t2`: one step **below** `occ_reforge`, so OTC stays weaker than OCC at the reforged tier too |
| `occ_reforge`, `omc_mod`, `oec_t2`, `cac_t1`, `bio_t3`, `odc_t3` | Below persona |
| `odc_t4`, `heroic`, `trophy`, `cac_t2`, `bio_t4` | Cataphract / persona |
| `omg` | Slightly above `odc_t4` |
| `mech` | Same as `omc` (kept so every rung has a row; no Core worn suit uses it yet) |

CE reference points (sharp / blunt, mm / MPa): recon 16 / 34, marine 20 / 45, cataphract 28 / 60. Helmets: recon 12 / 26, marine 16 / 36, cataphract 22 / 50. Heat stays on the vanilla 0–2 scale (recon 0.46, marine 0.54, cataphract 0.60).

Helmets use the set’s rung with a helmet table on the same ladder (recon → marine → cataphract helmet values), not a second ad-hoc ladder.

**Coverage templates** (`CombatExtended.PartialArmorExt` multipliers; Obsidia pieces do not cover hands or feet):

| Template | Rungs | Parts |
|---|---|---|
| light | `proto`, `otc` | body: neck 0.60, arm 0.80, leg 0.90 · helmet: eye 0.70, nose/jaw 0.50 |
| marine | `occ`, `odc_t1`, `omc`, `mech`, `oec`, `oe` | body: neck 0.80, arm 0.90 · helmet: eye/nose 0.80 |
| heavy | `odc_t2`, `otc_t2` and everything above | body: neck 0.90 · helmet: eye 0.90 |

**Carry capacity:** CE counts worn armor mass against inventory weight. CE’s own recon / marine / cataphract armor add `CarryWeight` / `CarryBulk` (50 / 8, 80 / 10, 100 / 20). Body armor gets the matching offset for its rung so a 50–80 kg suit does not overload the wearer. Helmets get none.

## What the generator writes

`Patches/Apparel/OE_Armor.xml` and `Patches/Apparel/OE_Helmets.xml` only. No new `Defs/` for this slice.

Per member:

- Set `ArmorRating_Sharp` / `Blunt` / `Heat`, `Mass`, `Bulk`, `WornBulk` to the CE-scale values from the armor (or helmet) rung table. Each stat is a conditional replace-or-add, because many Core pieces inherit these from a parent instead of defining them.
- Body armor only: set `equippedStatOffsets` `CarryWeight` / `CarryBulk` the same way
- Add `CombatExtended.PartialArmorExt` with the rung’s coverage template, except on children that inherit it from a catalogued concrete parent

Do not add CE apparel comps for shields (out of scope). Do not retarget `recipeUsers`. Do not emit pawnKind or trader patches for clothing. Leave Obsidia’s own `equippedStatOffsets` (move speed, pain shock, etc.) alone.

## Tests

- OCC body armor sharp sits in CE marine neighbourhood
- OTC body armor sharp (and blunt) is strictly below OCC, at both the base and the reforged tier
- A catalogued helmet gets the helmet `PartialArmorExt` template, not the body template
- Body armor gets `CarryWeight`; helmets do not
- A child of a catalogued concrete parent gets stats but no second `PartialArmorExt`
- Excluded `*Shield*` / uniform / `Grenade_*` defNames are absent from generated patches
- The apparel validator fails if an in-scope Core apparel def is missing, duplicated, listed despite being excluded, or inherits from a parent with a different coverage template

## Playtest bar

1. Colonist in OCC armor + helmet takes CE-plausible hits (not vanilla sponge, not paper).
2. Same pawn in OTC armor is clearly squishier than OCC.
3. Headshots care about the helmet; removing it makes the head the weak point.
4. A pawn in OCC armor is not overweight from the armor alone (carry offset works).
5. Shield / barrier / grenadier variants still work as Obsidia made them; the ones built on a catalogued piece show that piece’s CE armor numbers.

## Later slices (not this spec)

Pawn/animal/mech bodies; turrets; vehicles; DLC apparel; shield/barrier CE comps; optional CE bench recipes.
