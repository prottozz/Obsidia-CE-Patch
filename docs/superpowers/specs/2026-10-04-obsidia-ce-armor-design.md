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
- job / worker gear: miner, medic, constructor, trader, worker helmets and worker shells (`ODC_Helmet_Miner`, `ODC_Helmet_Constructor`, `ODC_Helmet_Medic`, `ODC_Helmet_Trader`, `EGO_Helmet_Exohelm_Worker`, `EGO_Armor_Shell_Worker`, and any later Core def that is clearly the same role)

Stalker / trophy / EGO melee-ranged combat shells **are** in scope.

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
| `occ_reforge`, `omc_mod`, `oec_t2`, `otc_t2`, `cac_t1`, `bio_t3`, `odc_t3` | Below persona |
| `odc_t4`, `heroic`, `trophy`, `cac_t2`, `bio_t4` | Cataphract / persona |
| `omg` | Slightly above `odc_t4` |

Helmets use the set’s rung with a helmet template: same CE analogue, `PartialArmor` focused on head/neck, ratings in the same neighbourhood as that rung’s CE helmet (not a second ad-hoc ladder).

## What the generator writes

`Patches/Apparel/OE_Armor.xml` and `Patches/Apparel/OE_Helmets.xml` only. No new `Defs/` for this slice.

Per member:

- Replace vanilla `ArmorRating_Sharp` / `Blunt` / `Heat` with CE-scale values from the armor (or helmet) rung table
- Set `Mass`, `Bulk`, `WornBulk`
- Add `modExtensions` → `CombatExtended.PartialArmor`
  - Body armor: torso / neck / shoulders high; arms / legs partial (marine vs cataphract coverage templates by rung)
  - Helmets: head / neck

Do not add CE apparel comps for shields (out of scope). Do not retarget `recipeUsers`. Do not emit pawnKind or trader patches for clothing.

## Tests

- OCC body armor sharp sits in CE marine neighbourhood
- OTC body armor sharp (and blunt) is strictly below OCC
- A catalogued helmet gets the helmet `PartialArmor` template, not the body template
- Excluded `*Shield*` / uniform / `Grenade_*` defNames are absent from generated patches
- `validate_catalog` fails if an in-scope Core apparel def is missing, duplicated, or listed despite being excluded

## Playtest bar

1. Colonist in OCC armor + helmet takes CE-plausible hits (not vanilla sponge, not paper).
2. Same pawn in OTC armor is clearly squishier than OCC.
3. Headshots care about the helmet; removing it makes the head the weak point.
4. Unpatched shield / barrier / grenadier items still exist in-game; this slice does not CE them.

## Later slices (not this spec)

Pawn/animal/mech bodies; turrets; vehicles; DLC apparel; shield/barrier CE comps; optional CE bench recipes.
