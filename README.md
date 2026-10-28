# Obsidia Expansion - Combat Extended Patch

Standalone CE patch for Obsidia Expansion Core, built for RimWorld **1.7** (CE `1.7-Test` branch). Catalog in `catalog/`, generator in `Tools/`. RimWorld loads `1.7/Defs/` and `1.7/Patches/` only; the generator writes there.

## Ammo-network bridge (C#)

Obsidia's turret ammo network (VEF PipeSystem `OE_AmmoNet`) only fills `CompRefuelable`, which CE turrets ignore. `Source/ObsidiaCEAmmoNet` is a small comp (no Harmony) that pours network ammo into CE turret magazines at Obsidia's kit-to-shots rate. It ships prebuilt in `1.7/Mods/AmmoNet/Assemblies/` and loads only when VEF is active (`LoadFolders.xml`).

Rebuild (needs the .NET 10 SDK):

```
dotnet build Source/ObsidiaCEAmmoNet -c Release -p:CombatExtendedDll=<CE 1.7 CombatExtended.dll>
```

`PipeSystemDll` defaults to `../references/294100/2023507013/1.7/Assemblies/PipeSystem.dll`; override with `-p:PipeSystemDll=...`.
