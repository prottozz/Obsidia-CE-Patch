using System;
using CombatExtended;
using PipeSystem;
using RimWorld;
using Verse;

namespace ObsidiaCEAmmoNet;

/// <summary>
/// Connects a CE turret to an Obsidia ammo pipe network. Added by
/// 1.7/Mods/AmmoNet/Patches to every OE turret that used OE_AmmoKit fuel.
/// </summary>
public class CompProperties_AmmoNetFeed : CompProperties_Resource
{
    /// <summary>Shots per network unit (one OE_AmmoKit). Obsidia's fuelMultiplier.</summary>
    public float shotsPerUnit = 1f;

    /// <summary>Top the magazine up once it drops below this fraction. Obsidia's autoRefuelPercent.</summary>
    public float refillBelow = 0.75f;

    /// <summary>Ticks between network checks.</summary>
    public int checkInterval = 250;

    public CompProperties_AmmoNetFeed()
    {
        compClass = typeof(CompAmmoNetFeed);
    }
}

public class CompAmmoNetFeed : CompResource
{
    public CompProperties_AmmoNetFeed FeedProps => (CompProperties_AmmoNetFeed)props;

    public override void CompTick()
    {
        base.CompTick();
        if (parent.IsHashIntervalTick(Math.Max(1, FeedProps.checkInterval)))
        {
            TryFeed();
        }
    }

    public override void CompTickRare()
    {
        base.CompTickRare();
        TryFeed();
    }

    /// <summary>Pull network ammo into the turret magazine. Returns shots loaded.</summary>
    public int TryFeed()
    {
        if (parent is not Building_TurretGunCE turret || !turret.Spawned || turret.isReloading)
        {
            return 0;
        }
        CompAmmoUser ammo = turret.CompAmmo;
        PipeNet net = PipeNet;
        if (ammo == null || !ammo.HasMagazine || !ammo.UseAmmo || net == null)
        {
            return 0;
        }
        if (ammo.CurMagCount > 0 && ammo.CurrentAmmo != ammo.SelectedAmmo)
        {
            return 0; // player is switching ammo type: let the normal CE reload handle it
        }
        if (ammo.CurMagCount >= ammo.MagSize * FeedProps.refillBelow)
        {
            return 0;
        }
        int shots = ShotsToLoad(ammo.MagSize - ammo.CurMagCount, net.Stored, FeedProps.shotsPerUnit);
        if (shots <= 0)
        {
            return 0;
        }
        net.DrawAmongStorage(shots / FeedProps.shotsPerUnit, out _, null);
        if (ammo.CurMagCount == 0 || ammo.CurrentAmmo == null)
        {
            ammo.CurrentAmmo = ammo.SelectedAmmo;
        }
        ammo.CurMagCount += shots;
        return shots;
    }

    /// <summary>Whole shots that fit the gap and that the stored network units can pay for.</summary>
    public static int ShotsToLoad(int missing, float storedUnits, float shotsPerUnit)
    {
        if (missing <= 0 || storedUnits <= 0f || shotsPerUnit <= 0f)
        {
            return 0;
        }
        double affordable = Math.Floor(storedUnits * (double)shotsPerUnit + 1e-6);
        return (int)Math.Min(missing, affordable);
    }

    public override string CompInspectStringExtra()
    {
        PipeNet net = PipeNet;
        string baseText = base.CompInspectStringExtra();
        if (net == null)
        {
            return baseText;
        }
        string line = $"Ammo network: {net.Stored:0.#} kits stored, {FeedProps.shotsPerUnit:0.##} shots per kit";
        return baseText.NullOrEmpty() ? line : baseText + "\n" + line;
    }
}
