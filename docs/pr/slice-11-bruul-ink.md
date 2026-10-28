# Slice 11 — Bruul ink (blunt glob + elemental secondary)

Branch: `feat/slice-11-bruul-ink-blunt` → `main`

## Summary

- Convert the four Bruuls' ink from vanilla `Verb_Shoot` to CE: `Verb_ShootCE` plus a dedicated CE projectile. Race Sharp/Blunt and `OEBruulLike` BodyDef were already done; this slice is the spit.
- Non-explosive ink is a **blunt glob** (AP blunt 6, sharp 0) with Obsidia's element as CE `secondaryDamage` (`OTCAcid` / `OTCCryo` / `EMP` / `Flame`). Original Obsidia `Bullet_Bruul_*` defs are left untouched; copies are `Bullet_OE_Bruul_*_CE`.
- EMP ink gets `empShieldBreakChance` 0.15; fire ink is incendiary. Graphic, speed, range, and minRange stay from Obsidia.
- Generator walks catalogued races' ranged verbs (`Tools/oe_ce/emit_race_verbs.py`). Explosive spit (none on Bruuls today) would reuse slice 10 blast rules.

## Changelog

### Verbs

- `1.7/Patches/Races/OE_RaceVerbs.xml` replaces `<verbs>` on `OE_Bruul_Acid`, `Cryo`, `EMP`, `Fire` with `CombatExtended.VerbPropertiesCE`.
- Keeps Obsidia warmup, accuracy, range 23.9, minRange 2.0, commonality 0.8.

### Projectiles

- `Bullet_OE_Bruul_Acid_CE` — Blunt 6 + `OTCAcid` 6
- `Bullet_OE_Bruul_Cryo_CE` — Blunt 6 + `OTCCryo` 6
- `Bullet_OE_Bruul_EMP_CE` — Blunt 6 + `EMP` 6, shield-break 0.15
- `Bullet_OE_Bruul_Fire_CE` — Blunt 6 + `Flame` 6, incendiary

### Out of this slice

- Other race spit (slimes, etc.) — pipeline exists, not catalogued here.
- VVE vehicles.
- `OEC_Armor_M_Grenadier`.

## Test plan

- [ ] Acid/Cryo/EMP/Fire Bruuls spit CE ink (blunt impact + elemental secondary), not vanilla `Verb_Shoot`
- [ ] Fire Bruul can start fires; EMP Bruul can tick shields
- [ ] Core + CE, no extra DLC: Bruuls load clean
- [ ] Race Sharp/Blunt and `OEBruulLike` coverage unchanged
- [x] `python -m pytest tests -q` from Tools/ — 240 passed
