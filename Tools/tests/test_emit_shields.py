from oe_ce.emit_shields import emit_innate_xml, emit_upgrade_xml, emit_worn_handheld_xml
from oe_ce.scan_shields import CoreShield, HANDHELD, INNATE, UPGRADE, WORN
from oe_ce.shield_models import (
    HandheldSet,
    InnateSet,
    ShieldCatalog,
    ShieldMember,
    UpgradeSet,
    WornSet,
)


def test_oes_emits_partial_armor_and_heroic_sharp_occ_does_not():
    cat = ShieldCatalog(
        worn=[
            WornSet(
                "oes",
                "heroic",
                "guardian",
                "emit",
                [ShieldMember("OES_Armor_Shield")],
            ),
            WornSet(
                "occ",
                "occ_reforge",
                "guardian",
                "inherit",
                [ShieldMember("OCC_Armor_M_Shield")],
            ),
            WornSet(
                "omg",
                "omg",
                "protector",
                "skip",
                [ShieldMember("OMG_Armor_Corsair")],
            ),
        ]
    )
    scanned = {
        "OES_Armor_Shield": CoreShield("OES_Armor_Shield", WORN, True),
        "OCC_Armor_M_Shield": CoreShield(
            "OCC_Armor_M_Shield", WORN, True, "OCC_Armor_M"
        ),
        "OMG_Armor_Corsair": CoreShield("OMG_Armor_Corsair", WORN, False),
    }
    xml = emit_worn_handheld_xml(cat, scanned)
    assert xml.index('defName="OCC_Armor_M_Shield"') < xml.index('defName="OES_Armor_Shield"')
    oes = xml.split('defName="OES_Armor_Shield"')[1].split('defName="OMG_Armor_Corsair"')[0]
    assert "CombatExtended.PartialArmorExt" in oes or xml.count("PartialArmorExt") == 1
    assert "<ArmorRating_Sharp>28</ArmorRating_Sharp>" in xml
    assert '<xpath>Defs/ThingDef[defName="OCC_Armor_M_Shield"]' in xml
    occ_block = xml.split('defName="OCC_Armor_M_Shield"')[1].split('defName="OES_Armor_Shield"')[0]
    assert "PartialArmorExt" not in occ_block
    assert "<EnergyShieldEnergyMax>" in xml
    corsair = xml.split('defName="OMG_Armor_Corsair"')[1]
    assert "PartialArmorExt" not in corsair
    assert "<EnergyShieldEnergyMax>2.07</EnergyShieldEnergyMax>" in xml


def test_oec_worn_wrapped_royalty():
    cat = ShieldCatalog(
        worn=[
            WornSet(
                "oec",
                "oec_t2",
                "guardian",
                "emit",
                [ShieldMember("OEC_Armor_M_Shield")],
                may_require="Ludeon.RimWorld.Royalty",
            )
        ]
    )
    scanned = {"OEC_Armor_M_Shield": CoreShield("OEC_Armor_M_Shield", WORN, True)}
    xml = emit_worn_handheld_xml(cat, scanned)
    assert 'MayRequire="Ludeon.RimWorld.Royalty"' in xml
    assert "<li Class=" in xml
    assert "<operations>" in xml
    assert "<Operation Class=" not in xml.split("<operations>")[1].split("</operations>")[0]


def test_handheld_converts_vef_to_ce():
    cat = ShieldCatalog(
        handheld=[
            HandheldSet(
                "odc",
                "odc_t2",
                "small",
                [ShieldMember("ODC_Shield_Small")],
                may_require="OskarPotocki.VanillaFactionsExpanded.Core",
            ),
            HandheldSet(
                "oec",
                "oec",
                "small",
                [ShieldMember("OEC_Shield_Small")],
                may_require="OskarPotocki.VanillaFactionsExpanded.Core,Ludeon.RimWorld.Royalty",
            ),
        ]
    )
    scanned = {
        "ODC_Shield_Small": CoreShield(
            "ODC_Shield_Small", HANDHELD, tex_path="Things/Shield/ODC"
        ),
        "OEC_Shield_Small": CoreShield(
            "OEC_Shield_Small", HANDHELD, tex_path="Things/Shield/OEC"
        ),
    }
    xml = emit_worn_handheld_xml(cat, scanned)
    assert "<thingClass>CombatExtended.Apparel_Shield</thingClass>" in xml
    assert 'ThingDef[@Name="OEShieldBase"]' in xml
    assert 'ThingDef[@Name="OEShieldBaseNQ"]' in xml
    assert 'Class="VEF.Apparels.CompProperties_Shield"' in xml
    assert "PatchOperationRemove" in xml
    assert "CombatExtended.ShieldDefExtension" in xml
    assert "<li>Hands</li>" in xml
    assert "CombatExtended.PawnRenderNode_Apparel" in xml
    assert "Things/Shield/ODC" in xml
    assert 'MayRequire="OskarPotocki.VanillaFactionsExpanded.Core,Ludeon.RimWorld.Royalty"' in xml


def test_innate_queen_is_biotech_sequence_of_li():
    cat = ShieldCatalog(
        innate=[
            InnateSet(
                "queen",
                "warqueen",
                [ShieldMember("OE_Mech_ArachnaQueen")],
                may_require="Ludeon.RimWorld.Biotech",
            )
        ]
    )
    xml = emit_innate_xml(cat)
    assert 'MayRequire="Ludeon.RimWorld.Biotech"' in xml
    assert "<EnergyShieldEnergyMax>4.5</EnergyShieldEnergyMax>" in xml
    assert "<EnergyShieldRechargeRate>0.75</EnergyShieldRechargeRate>" in xml
    inner = xml.split("<operations>")[1].split("</operations>")[0]
    assert "<li Class=" in inner
    assert "<Operation " not in inner
    assert "ProjectileInterceptor" not in xml


def test_upgrade_targets_mechupgradedef():
    cat = ShieldCatalog(
        upgrades=[
            UpgradeSet(
                "mod",
                2.5,
                [ShieldMember("OE_MechUpgrade_Module_Shield_O")],
                may_require="GoGaTio.MechanoidUpgrades",
            )
        ]
    )
    xml = emit_upgrade_xml(cat)
    assert 'MayRequire="GoGaTio.MechanoidUpgrades"' in xml
    assert 'MU.MechUpgradeDef[defName="OE_MechUpgrade_Module_Shield_O"]' in xml
    assert "<EnergyShieldEnergyMax>2.5</EnergyShieldEnergyMax>" in xml
    assert "<factor>2.5</factor>" in xml
    assert 'UpgradeCompProperties_ShieldUpgrade' in xml
