from pathlib import Path

from oe_ce.shield_load import load_shield_catalog
from oe_ce.shield_rungs import GUARDIAN, PROTECTOR, HANDHELD_SIZES, INNATE_ENERGY

ROOT = Path(__file__).resolve().parents[2]


def test_load_repo_catalog_covers_spec_inventory():
    cat = load_shield_catalog(ROOT / "catalog")
    worn = {m.def_name: s for s in cat.worn for m in s.members}
    assert worn["OCC_Armor_M_Shield"].role == GUARDIAN
    assert worn["OCC_Armor_M_Shield"].plate == "inherit"
    assert worn["OCC_Armor_M_Shield"].member_rung(worn["OCC_Armor_M_Shield"].members[0]) == "occ_reforge"
    assert worn["OES_Armor_Shield"].plate == "emit"
    assert worn["OES_Armor_Shield"].rung == "heroic"
    assert worn["OMG_Armor_Corsair"].plate == "skip"
    assert worn["OEC_Armor_M_Barrier"].may_require == "Ludeon.RimWorld.Royalty"
    assert worn["OE_Trophy_Grimoire_Defender"].may_require == (
        "OskarPotocki.VanillaFactionsExpanded.Core"
    )
    assert worn["OE_Trophy_Grimoire_Mechanitor"].role == PROTECTOR
    assert {s.role for s in cat.worn} <= {GUARDIAN, PROTECTOR}

    handheld = {m.def_name: s for s in cat.handheld for m in s.members}
    assert set(handheld) == {
        "ODC_Shield_Small",
        "OEC_Shield_Small",
        "OES_Shield_Small",
        "ODC_Shield_Medium",
        "OTC_Shield_Medium",
        "OMC_Shield_Medium",
        "EGO_Shield_Medium",
        "OMG_Shield_Medium",
        "OCC_Shield_Big",
        "CAC_Shield_Big",
        "OES_Shield_Big",
    }
    assert handheld["OEC_Shield_Small"].may_require == (
        "OskarPotocki.VanillaFactionsExpanded.Core,Ludeon.RimWorld.Royalty"
    )
    assert handheld["OES_Shield_Small"].size in HANDHELD_SIZES
    oes_small = next(m for m in handheld["OES_Shield_Small"].members if m.def_name == "OES_Shield_Small")
    assert oes_small.mass == 4

    innate = {m.def_name: s for s in cat.innate for m in s.members}
    assert set(innate) == {
        "OE_Mech_ArachnaQueen",
        "OE_Mech_CrimsonArachna",
        "OE_Mech_FallenLegion",
        "OE_Mech_OMG_Dominator",
    }
    assert innate["OE_Mech_ArachnaQueen"].analogue in INNATE_ENERGY
    assert innate["OE_Mech_ArachnaQueen"].may_require == "Ludeon.RimWorld.Biotech"

    assert len(cat.upgrades) == 1
    up = cat.upgrades[0]
    assert up.factor == 2.5
    assert up.members[0].def_name == "OE_MechUpgrade_Module_Shield_O"
    assert up.may_require == "GoGaTio.MechanoidUpgrades"


def test_catalog_def_names_are_unique():
    cat = load_shield_catalog(ROOT / "catalog")
    names = list(cat.def_names())
    assert len(names) == len(set(names))
    assert len(names) == 24 + 11 + 4 + 1
