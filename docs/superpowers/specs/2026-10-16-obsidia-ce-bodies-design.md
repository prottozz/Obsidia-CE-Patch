# Obsidia CE Patch — Slice 3: Core Race Bodies

**Date:** 2026-10-16  
**Repo:** [prottozz/Obsidia-CE-Patch](https://github.com/prottozz/Obsidia-CE-Patch)  
**Status:** Draft for user review (brainstorming gate)

Standalone Combat Extended compatibility for **Obsidia Expansion Core** race ThingDefs (animals, elder beasts, slimes, mechanoids) plus four Biotech mechanoid bosses. Slices 1 and 2 already patched Core guns, melee, ammo, raid magazines, combat armor, and helmets. This spec does not change those.

## Goal

Every Core race ThingDef uses Combat Extended `bodyShape`, hide/plating on the CE scale, `ToolCE` melee, and `CompProperties_ArmorDurability`, so wildlife and mechs are neither vanilla sponges nor paper against CE guns. Races are grouped into named species sets and balanced from a **CE analogue table** (warg, thrumbo, megaspider, centipede, …).

## Out of scope

- Colonist / humanlike races (`Human` already has CE's own patch)
- Obsidia `BodyDef` / `BodyPartDef` trees (`OERaptorLike`, `OEDominator`, slime gel, …). Coverage and part health stay as Core wrote them.
- Bruul (and similar) built-in projectile ThingDefs sitting in race XML. Those wait for a later ammo slice.
- PawnKind loadouts beyond what slice 1 already emits
- Turrets, vehicles
- Other Royalty / Ideology / Biotech / Anomaly / Odyssey / VFE / Gravship / EBSG races (Legion Guard/Drone, Arachna drones, New* pawnKinds). The four Biotech bosses below are in scope.
- Shield / barrier / grenadier apparel, DLC apparel
- New armor, gun, or melee patches for worn equipment

## Dependencies

Unchanged: RimWorld 1.6, `prottozz.ObsidiaCEPatch`, requires `CETeam.CombatExtended` and `ObsidiaExpansion.Core`, `loadAfter` both. Harmony is not required (XML only).

## Architecture

RimWorld still loads only `About/`, `Defs/`, and `Patches/`. Catalog and `Tools/` stay generator-only.

**Data flow:** `catalog/races.yaml` + a read of Obsidia `1.6/Core` `Defs/ThingDefs_Races` (and `1.6/Biotech/Defs/ThingDefs_Races` when that folder exists) → generator → committed `Patches/Races/OE_Animals.xml` and `Patches/Races/OE_Mechanoids.xml`. Players do not need Python. Do not hand-edit generated XML.

**Failure policy:** generator exits non-zero if an in-scope Core race is missing from the catalog, if two entries share a `defName`, or if a catalogued `defName` is not a scanned race ThingDef. Biotech bosses are required in the catalog; if the Biotech races dir is missing they are still catalogued and their patch ops carry `MayRequire="Ludeon.RimWorld.Biotech"` so a Core-only install does not fail.

## Catalog

Sets are the race equivalent of armor kits. They do **not** share an item; they exist so a species (Direwolf + Elder Direwolf, all Dominators, all slimes) stays on one analogue unless a member overrides it.

```yaml
sets:
  - id: direwolf
    analogue: warg
    bodyShape: Quadruped
    members:
      - defName: OE_Direwolf
      - defName: OE_Elder_Direwolf
        analogue: thrumbo
  - id: dominator
    analogue: walker
    bodyShape: Humanoid
    members:
      - defName: OE_Mech_OCC_Dominator
      - defName: OE_Mech_OMG_Dominator
        analogue: centipede
```

Member fields: `defName` (required), optional `analogue`, optional `bodyShape`, optional `tools` (list of ToolCE rows: `label`, `capacities`, `linkedBodyPartsGroup`, plus optional `power` / `cooldownTime` / AP overrides). If `tools` is omitted, the generator converts Core's existing `<tools>` in place: same labels, capacities, linked groups, power and cooldown; `Class="CombatExtended.ToolCE"`; a single vanilla `armorPenetration` becomes `armorPenetrationSharp` when any capacity is Scratch, Bite, Cut, Stab, or Poke, otherwise `armorPenetrationBlunt`. Catalog `tools:` fully replaces Core's list.

Shared set ids with armor (`occ`, `omg`) are allowed; they are different catalogs.

## Scanner

Walk Core `Defs/ThingDefs_Races/**/*.xml`, then Biotech `Defs/ThingDefs_Races/**/*.xml` if present. A def is in scope when it is a non-abstract `ThingDef` with a `defName` whose parent chain (via `ParentName`, same walk as apparel) has a `<race>` node. Skip `PawnKindDef`. Skip projectile / bullet ThingDefs (no `<race>` in the chain). From Biotech, only these four bosses are in scope: `OE_Mech_ChaosLord`, `OE_Mech_ArachnaQueen`, `OE_Mech_CrimsonArachna`, `OE_Mech_FallenLegion`. Record `kind` as `mechanoid` if the nearest `race/fleshType` is `Mechanoid` or the defName starts `OE_Mech_`, otherwise `animal`. Record the nearest concrete parent the same way slice 2 did, for inherited extensions.

Real Core yields **78** concrete races: **57** animals (including 5 that inherit `<race>`: Armagon, Hootie, Scorpid ×2, Sharkaradon) and **21** mechanoids. Biotech adds **4** bosses (82 total when Biotech is present). The four Bruul `Bullet_*` defs are out of scope. `OE_Mech_CAC_Arachna` in Core is the medium cult walker, not the Crimson Arachna boss.

## Analogue table

Keyed independently of the gun and armor rung names. Each row is a named CE vanilla analogue. Numbers are CE's own patches unless noted as interpolation.

| analogue | bodyShape default | sharp | blunt | heat | dodge / crit / parry | durability | notes |
|---|---|---|---|---|---|---|---|
| hide | Quadruped | 0.05 | 0.075 | — | 0.16 / 0.14 / 0.10 | 400 | small pets, jelly slime (bear-cub hide) |
| warg | Quadruped | 0.10 | 0.15 | — | 0.23 / 0.20 / 0.11 | 700 | Direwolf, Raptor |
| cougar | Quadruped | 0.10 | 0.15 | — | 0.22 / 0.18 / 0.10 | 575 | interpolates CE cougar durability |
| megascarab | QuadrupedLow | 0.70 | 2.25 | — | 0.08 / 0.12 / 0.10 | 150 | Bruul, Scorpid, cheap slime metals |
| megaspider | QuadrupedLow | 4 | 10 | — | 0.10 / 0.20 / 0.15 | 925 | Arachna animal, Tionant |
| thrumbo | QuadrupedTall | 14 | 21 | 0.60 | 0.10 / 0.82 / 0.48 | 3000 | Elder Direwolf / Raptor / Ogren / Armagon / Sharkaradon, mythril/obsidian slime |
| walker | Humanoid | 4 | 6 | 0 | 0.13 / 0.12 / 0.09 | 800 | CE `BaseMechanoidWalker` (scyther/lancer); Necroframe, OCC/OMC Arachna, OCC Dominator |
| pikeman | Quadruped | 7 | 15 | 0 | 0.04 / 0.13 / 0.15 | 1200 | ODC light Dominator, OEC |
| centipede | QuadrupedLow | 20 | 45 | 0.25 | 0.03 / 0.26 / 0.52 | 3660 | Dark Crusader, OMG Dominator, ODC heavy |
| diabolus | QuadrupedLow | 24 | 54 | 0.50 | 0.03 / 0.42 / 0.64 | 4250 | CE Diabolus (inherits SuperHeavy); Chaos Lord |
| warqueen | QuadrupedLow | 24 | 54 | 0.50 | 0.02 / 0.22 / 0.64 | 4600 | CE Warqueen (inherits SuperHeavy); Arachna Queen |
| warqueen_plus | QuadrupedLow | 26 | 58 | 0.50 | 0.02 / 0.22 / 0.64 | 5000 | Crimson Arachna: one step above Warqueen |
| apocriton | Humanoid | 24 | 60 | 0.50 | 0.07 / 0.13 / 0.13 | 3100 | CE Apocriton (not used on an Obsidia def; reference row) |
| apocriton_plus | Humanoid | 26 | 64 | 0.50 | 0.07 / 0.13 / 0.13 | 3400 | Fallen Legion: one step above Apocriton |

Heat is omitted (`—`) when CE does not set it on that analogue; the emitter then leaves Core's heat alone.

Faction Dominator / Arachna ladder: OTC elemental and OMC → `walker`; OCC → `walker`; OEC / ODC light / CAC Arachna → `pikeman`; ODC heavy / OMG / Dark Crusader → `centipede`. Necroframe melee and ranged → `walker`. Biotech bosses: `OE_Mech_ChaosLord` → `diabolus` with **bodyShape Humanoid** (OEDominator is bipedal; CE Diabolus is QuadrupedLow); `OE_Mech_ArachnaQueen` → `warqueen`; `OE_Mech_CrimsonArachna` → `warqueen_plus`; `OE_Mech_FallenLegion` → `apocriton_plus`. Elder beasts always `thrumbo`. Adult Direwolf / Raptor → `warg`. Ogren adult → `thrumbo` (body size). Tionant adult → `megaspider`; Elder Tionant → `thrumbo`. Remaining small animals (Astrinx, Rosner, Snapper, Caterpillar, Hootie) → `hide`. Slimes: jelly/herbal/fungus/beer/chemfuel/neutroamine/ambrosia/jumy → `hide`; steel/silver/gold/jade/bone/hauler → `megascarab`; uranium/platinum/syntherius/ancient/luciferium → `megaspider`; mythril/obsidian/nullium/torraxin/joltixin → `thrumbo`.

`bodyShape` defaults from the analogue; a set or member may override. Allowed values are CE's stock list: `Humanoid`, `HumanoidWide`, `Quadruped`, `QuadrupedLow`, `QuadrupedTall`, `Serpentine`, `Birdlike`. Hootie → `Birdlike`. Bruul / Scorpid / Arachna animal → `QuadrupedLow`. Slime → `QuadrupedLow`. Sharkaradon → `Serpentine`. Dark Crusader, Dominator, Chaos Lord, Fallen Legion → `Humanoid` (`OEDominator` is bipedal). Arachna mech and both Arachna Queens → `QuadrupedLow`. Necroframe → `Humanoid`.

## Per-race patch

For each catalogued defName, in this order:

1. `PatchOperationAddModExtension` `CombatExtended.RacePropertiesExtensionCE` with `<bodyShape>`. Skip if the concrete parent is also catalogued and shares the same bodyShape (RimWorld copies the extension).
2. Conditional replace-or-add under `statBases`: `ArmorRating_Sharp`, `ArmorRating_Blunt`, `ArmorRating_Heat` (if the analogue has heat), `MeleeDodgeChance`, `MeleeCritChance`, `MeleeParryChance`. Do not touch `MoveSpeed`, `MarketValue`, or Obsidia's other stats.
3. Replace `<tools>` with `CombatExtended.ToolCE` rows from the catalog (or the converted Core tools). Capacities and `linkedBodyPartsGroup` must match a group that exists on that race's BodyDef; the generator does not validate BodyDefs beyond copying Core's groups.
4. Ensure `<comps />`, then add `CombatExtended.CompProperties_ArmorDurability` with `Durability` from the analogue, `Regenerates` true, `RegenInterval` 600 / `RegenValue` 5 for animals, 1250 / 5 for mechanoids, `MinArmorPct` 0.5. Mechanoids also get `Repairable` true with `Steel` 5 + `Plasteel` 5, `RepairTime` 300, `RepairValue` 200, matching CE walkers. Skip the durability add if the concrete parent is catalogued (inherited).

Do not add CE's mechanoid `CompAmmoGiver` / `CompProperties_MechAmmo` / `PartialArmorExt` on sensors: Dark Crusader and Dominators already receive ammo via slice 1 pawnKind loadouts where they carry guns, and their BodyDefs do not use vanilla `SightSensor` parts. Do not retune `EnergyShieldEnergyMax` / `EnergyShieldRechargeRate` on the queens or Fallen Legion.

Each of the four Biotech boss operations sets `MayRequire="Ludeon.RimWorld.Biotech"` on the outer `PatchOperation`.

Do not change `baseHealthScale`. CE removes it on some vanilla mechs; leaving Obsidia's values avoids a silent HP collapse.

## Generator

`scan_races(core)` also accepts an optional Biotech races dir. `load_race_catalog`, `validate_race_catalog`, `race_stats(analogue)`, `emit_race_xml(sets, kind, core)`. `generate.py` requires Core `Defs/ThingDefs_Races`, appends race validation errors, writes the two patch files. `OE_CE_ALLOW_PARTIAL` still bypasses the exit.

Reuse `walk_parents`, `index_thingdefs`, and the conditional replace-or-add helpers from `emit_apparel.py` (extract a shared `_set_stat` / `_ensure_node` into `emit_common.py` if both modules would otherwise duplicate them; do not copy-paste the helpers).

## Tests

- Analogue table: every analogue used in the planned catalog has a row; `thrumbo.sharp == 14`; `centipede.sharp == 20`; `diabolus.sharp == 24` and `diabolus.blunt == 54`; `warqueen_plus.sharp > warqueen.sharp`; `apocriton_plus.sharp > apocriton.sharp`; `warg.sharp < megaspider.sharp < thrumbo.sharp`; `walker.sharp < pikeman.sharp < centipede.sharp < diabolus.sharp`.
- Scanner: fixture with an animal, a mech, a bullet, a PawnKind, an abstract base, and a child that inherits `<race>` from the abstract; real Core yields 57 animals and 21 mechanoids (78 total). `OE_Armagon` is in, `Bullet_Bruul_Acid` is out. With Biotech present, the scan also returns the four bosses.
- Catalog: missing Core race is an error; duplicate defName is an error; unknown analogue is an error; excluded bullet catalogued is an error; good catalog is clean.
- Emitter: Direwolf XML contains `bodyShape>Quadruped`, sharp 0.10, `Class="CombatExtended.ToolCE"`, `CompProperties_ArmorDurability`; Dark Crusader contains sharp 20, `Humanoid`, no `CompAmmoGiver`; child of a catalogued parent has stats but no second `RacePropertiesExtensionCE`.
- Coverage: `validate_race_catalog(load, scan(CORE)) == []`.
- Generator: writes both race files; fails without the Races dir; does not rewrite slice 1/2 output.

## Playtest bar

1. Spawn `OE_Direwolf`. Info card shows CE sharp ~0.10. A pistol FMJ wounds it; a marine rifle AP drops it in a few hits. Melee scratch uses ToolCE (no vanilla `armorPenetration` leftover).
2. Spawn `OE_Elder_Direwolf`. Same rifle takes many more shots; hide is thrumbo-grade (14 sharp).
3. Spawn `OE_Mech_DarkCrusader`. Marine rifle does little; cataphract-grade or AP is required. It still fires its slice 1 gun.
4. Spawn `OE_Slime_Jelly` and `OE_Slime_Mythril`. Jelly is hide-grade; mythril is thrumbo-grade.
5. With Biotech: `OE_Mech_ChaosLord` matches Diabolus plating (24/54); `OE_Mech_ArachnaQueen` matches Warqueen (24/54); `OE_Mech_CrimsonArachna` is a step above the Queen; `OE_Mech_FallenLegion` is a step above Apocriton (26/64).
6. Log has no patch errors naming `OE_Animals.xml` / `OE_Mechanoids.xml` or `RacePropertiesExtensionCE`.

If a check fails, change the catalog, analogue table, or emitter tests and regenerate. Do not hand-edit generated XML.

## Later slices (not this spec)

BodyDef coverage edits; Bruul built-in ammo; turrets; vehicles; remaining DLC races (Legion Guard/Drone, Arachna drones) and apparel; shield/barrier CE comps; optional CE bench recipes.
