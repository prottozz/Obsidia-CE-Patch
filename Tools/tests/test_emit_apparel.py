import xml.etree.ElementTree as ET

from oe_ce.apparel_models import ApparelMember, ApparelSet
from oe_ce.apparel_rungs import ARMOR, HELMET
from oe_ce.constants import ROYALTY_PACKAGE
from oe_ce.emit_apparel import emit_apparel_xml
from oe_ce.scan_apparel import CoreApparel, IsolatedApparel

CORE = {
    "OCC_Armor": CoreApparel("OCC_Armor", ARMOR),
    "OCC_Armor_M": CoreApparel("OCC_Armor_M", ARMOR),
    "OCC_Armor_M_Spacer": CoreApparel("OCC_Armor_M_Spacer", ARMOR, "OCC_Armor_M"),
    "OCC_Armor_M_Jump": CoreApparel("OCC_Armor_M_Jump", ARMOR, "OCC_Armor_M"),
    "OCC_Helmet": CoreApparel("OCC_Helmet", HELMET),
    "OEC_Armor": CoreApparel("OEC_Armor", ARMOR),
    "OEC_Armor_M": CoreApparel("OEC_Armor_M", ARMOR),
    "OEC_Armor_M_Spacer": CoreApparel("OEC_Armor_M_Spacer", ARMOR, "OEC_Armor_M"),
}


def test_occ_armor_gets_marine_stats_carry_and_coverage():
    xml = emit_apparel_xml([ApparelSet("occ", "occ", [ApparelMember("OCC_Armor")])], ARMOR, CORE)
    assert '<xpath>Defs/ThingDef[defName="OCC_Armor"]/statBases/ArmorRating_Sharp</xpath>' in xml
    assert "<ArmorRating_Sharp>20</ArmorRating_Sharp>" in xml
    assert "<ArmorRating_Blunt>45</ArmorRating_Blunt>" in xml
    assert "<ArmorRating_Heat>0.54</ArmorRating_Heat>" in xml
    assert "<Mass>50</Mass>" in xml
    assert "<Bulk>100</Bulk>" in xml
    assert "<WornBulk>15</WornBulk>" in xml
    assert "<CarryWeight>80</CarryWeight>" in xml
    assert "<CarryBulk>10</CarryBulk>" in xml
    assert "CombatExtended.PartialArmorExt" in xml
    assert "<li>Arm</li>" in xml
    assert "<ArmorRating_Sharp>0.90</ArmorRating_Sharp>" in xml


def test_missing_stat_nodes_are_added_not_assumed():
    xml = emit_apparel_xml([ApparelSet("occ", "occ", [ApparelMember("OCC_Armor")])], ARMOR, CORE)
    assert "<statBases />" in xml
    assert "<equippedStatOffsets />" in xml
    assert 'Class="PatchOperationTest"' in xml
    assert 'Class="PatchOperationConditional"' in xml
    assert '<nomatch Class="PatchOperationAdd">' in xml
    assert '<match Class="PatchOperationReplace">' in xml


def test_helmet_uses_helmet_template_and_no_carry():
    xml = emit_apparel_xml([ApparelSet("occ", "occ", [ApparelMember("OCC_Helmet")])], HELMET, CORE)
    assert "<ArmorRating_Sharp>16</ArmorRating_Sharp>" in xml
    assert "<ArmorRating_Blunt>36</ArmorRating_Blunt>" in xml
    assert "<li>Eye</li>" in xml
    assert "<li>Arm</li>" not in xml
    assert "CarryWeight" not in xml
    assert "equippedStatOffsets" not in xml


def test_child_of_catalogued_parent_gets_stats_but_no_second_extension():
    s = ApparelSet(
        "occ",
        "occ_reforge",
        [ApparelMember("OCC_Armor_M"), ApparelMember("OCC_Armor_M_Spacer")],
    )
    xml = emit_apparel_xml([s], ARMOR, CORE)
    assert xml.count("PatchOperationAddModExtension") == 1
    assert '<xpath>Defs/ThingDef[defName="OCC_Armor_M"]</xpath>' in xml
    assert (
        '<xpath>Defs/ThingDef[defName="OCC_Armor_M_Spacer"]/statBases/ArmorRating_Sharp</xpath>'
        in xml
    )
    assert "<ArmorRating_Sharp>26</ArmorRating_Sharp>" in xml


def test_output_is_valid_sorted_patch():
    s = ApparelSet(
        "occ",
        "occ",
        [ApparelMember("OCC_Armor_M", "occ_reforge"), ApparelMember("OCC_Armor")],
    )
    xml = emit_apparel_xml([s], ARMOR, CORE)
    root = ET.fromstring(xml.split("?>", 1)[1])
    assert root.tag == "Patch"
    assert xml.index('defName="OCC_Armor"]') < xml.index('defName="OCC_Armor_M"]')


def test_oec_armor_gets_marine_stats_and_coverage():
    xml = emit_apparel_xml(
        [ApparelSet("oec", "oec", [ApparelMember("OEC_Armor")], may_require=ROYALTY_PACKAGE)],
        ARMOR,
        CORE,
    )
    assert "<ArmorRating_Sharp>21</ArmorRating_Sharp>" in xml
    assert "<ArmorRating_Blunt>47</ArmorRating_Blunt>" in xml
    assert "<ArmorRating_Heat>0.55</ArmorRating_Heat>" in xml
    assert "<Mass>52</Mass>" in xml
    assert "CombatExtended.PartialArmorExt" in xml
    assert "<li>Arm</li>" in xml
    assert f'MayRequire="{ROYALTY_PACKAGE}"' in xml


def test_child_of_oec_m_skips_second_extension():
    s = ApparelSet(
        "oec",
        "oec_t2",
        [ApparelMember("OEC_Armor_M"), ApparelMember("OEC_Armor_M_Spacer")],
        may_require=ROYALTY_PACKAGE,
    )
    xml = emit_apparel_xml([s], ARMOR, CORE)
    assert xml.count("PatchOperationAddModExtension") == 1
    assert '<xpath>Defs/ThingDef[defName="OEC_Armor_M"]</xpath>' in xml
    assert (
        '<xpath>Defs/ThingDef[defName="OEC_Armor_M_Spacer"]/statBases/ArmorRating_Sharp</xpath>'
        in xml
    )


def test_jump_inherits_parent_coverage_and_uses_reforge_stats():
    s = ApparelSet(
        "occ",
        "occ_reforge",
        [
            ApparelMember("OCC_Armor_M"),
            ApparelMember("OCC_Armor_M_Jump", may_require=ROYALTY_PACKAGE),
        ],
    )
    xml = emit_apparel_xml([s], ARMOR, CORE)
    assert xml.count("PatchOperationAddModExtension") == 1
    jump = xml.split('MayRequire="Ludeon.RimWorld.Royalty"')[1]
    assert 'defName="OCC_Armor_M_Jump"]' in jump
    assert "<ArmorRating_Sharp>26</ArmorRating_Sharp>" in jump
    inner = jump.split("<operations>")[1].split("</operations>")[0]
    assert "<li Class=" in inner
    assert "<Operation Class=" not in inner
    assert 'defName="OCC_Armor_M"]' not in jump.split("<operations>")[1]


def test_core_ops_are_outside_mayrequire():
    xml = emit_apparel_xml(
        [
            ApparelSet(
                "occ",
                "occ",
                [
                    ApparelMember("OCC_Armor"),
                    ApparelMember("OCC_Armor_M_Jump", "occ_reforge", ROYALTY_PACKAGE),
                ],
            )
        ],
        ARMOR,
        CORE,
    )
    core_part = xml.split('MayRequire="Ludeon.RimWorld.Royalty"')[0]
    assert 'defName="OCC_Armor"]' in core_part
    assert 'defName="OCC_Armor_M_Jump"]' not in core_part


def test_odc_prestige_moves_psychic_stats_onto_the_wearer():
    core = {
        **CORE,
        "ODC_Armor_Duelist": CoreApparel("ODC_Armor_Duelist", ARMOR),
        "ODC_Armor_Duelist_Prestige": CoreApparel(
            "ODC_Armor_Duelist_Prestige", ARMOR, "ODC_Armor_Duelist"
        ),
        "ODC_Armor_Recon": CoreApparel("ODC_Armor_Recon", ARMOR),
        "ODC_Armor_Recon_Prestige": CoreApparel(
            "ODC_Armor_Recon_Prestige", ARMOR, "ODC_Armor_Recon"
        ),
    }
    xml = emit_apparel_xml(
        [
            ApparelSet(
                "odc_duelist",
                "odc_t3",
                [
                    ApparelMember("ODC_Armor_Duelist"),
                    ApparelMember(
                        "ODC_Armor_Duelist_Prestige", may_require=ROYALTY_PACKAGE
                    ),
                ],
            ),
            ApparelSet(
                "odc_recon",
                "odc_t2",
                [
                    ApparelMember("ODC_Armor_Recon"),
                    ApparelMember(
                        "ODC_Armor_Recon_Prestige", may_require=ROYALTY_PACKAGE
                    ),
                ],
            ),
        ],
        ARMOR,
        core,
    )
    for name in ("ODC_Armor_Duelist_Prestige", "ODC_Armor_Recon_Prestige"):
        assert f'{name}"]/statBases/PsychicSensitivityOffset</xpath>' in xml
        assert f'{name}"]/equippedStatOffsets/PsychicSensitivityOffset</xpath>' in xml
        assert f'{name}"]/statBases/PsychicEntropyRecoveryRate</xpath>' in xml
        assert f'{name}"]/equippedStatOffsets/PsychicEntropyRecoveryRate</xpath>' in xml
    assert "<PsychicSensitivityOffset>0.2</PsychicSensitivityOffset>" in xml
    assert "<PsychicEntropyRecoveryRate>0.083</PsychicEntropyRecoveryRate>" in xml
    assert 'defName="ODC_Armor_Duelist"]/statBases/PsychicSensitivityOffset' not in xml


def test_grenadier_is_isolated_from_parent_ce_plate():
    isolated = {
        "OEC_Armor_M_Grenadier": IsolatedApparel(
            "OEC_Armor_M_Grenadier",
            ARMOR,
            "OEC_Armor_M",
            1.15,
            0.55,
            0.55,
            10,
            (
                ("CarryingCapacity", "10"),
                ("PsychicSensitivityOffset", "0.20"),
                ("MoveSpeed", "0.1"),
            ),
            ROYALTY_PACKAGE,
        )
    }
    xml = emit_apparel_xml(
        [
            ApparelSet(
                "oec",
                "oec_t2",
                [ApparelMember("OEC_Armor_M")],
                may_require=ROYALTY_PACKAGE,
            )
        ],
        ARMOR,
        {**CORE, "OEC_Armor_M": CoreApparel("OEC_Armor_M", ARMOR)},
        isolated,
    )
    assert 'defName="OEC_Armor_M_Grenadier"]/statBases/ArmorRating_Sharp' in xml
    assert "<ArmorRating_Sharp>1.15</ArmorRating_Sharp>" in xml
    assert "<ArmorRating_Blunt>0.55</ArmorRating_Blunt>" in xml
    assert 'equippedStatOffsets Inherit="False"' in xml
    assert "<CarryingCapacity>10</CarryingCapacity>" in xml
    assert 'modExtensions Inherit="False"' in xml
    assert f'MayRequire="{ROYALTY_PACKAGE}"' in xml
    assert 'OEC_Armor_M_Grenadier"]/equippedStatOffsets/CarryWeight' not in xml
    assert 'OEC_Armor_M"]/equippedStatOffsets/CarryWeight' in xml


def test_grenadier_is_not_emitted_unless_parent_is_catalogued():
    isolated = {
        "OEC_Armor_M_Grenadier": IsolatedApparel(
            "OEC_Armor_M_Grenadier",
            ARMOR,
            "OEC_Armor_M",
            1.15,
            0.55,
            0.55,
            10,
            (("MoveSpeed", "0.1"),),
            ROYALTY_PACKAGE,
        )
    }
    xml = emit_apparel_xml(
        [ApparelSet("occ", "occ", [ApparelMember("OCC_Armor")])],
        ARMOR,
        CORE,
        isolated,
    )
    assert "OEC_Armor_M_Grenadier" not in xml


def test_royalty_members_are_wrapped_separately():
    s = ApparelSet(
        "oec",
        "oec",
        [ApparelMember("OEC_Armor"), ApparelMember("OEC_Armor_M", "oec_t2")],
        may_require=ROYALTY_PACKAGE,
    )
    xml = emit_apparel_xml([s], ARMOR, CORE)
    assert xml.count(f'MayRequire="{ROYALTY_PACKAGE}"') == 2
    assert xml.count("PatchOperationSequence") == 2
    assert xml.count('<nomatch Class="PatchOperationTest">') == 2
    first, rest = xml.split(f'MayRequire="{ROYALTY_PACKAGE}"', 1)
    second = rest.split(f'MayRequire="{ROYALTY_PACKAGE}"', 1)[1]
    assert 'defName="OEC_Armor_M"]' not in first
    assert 'defName="OEC_Armor"]' in rest.split(f'MayRequire="{ROYALTY_PACKAGE}"', 1)[0]
    assert 'defName="OEC_Armor"]' not in second.split("<operations>")[1].split("</operations>")[0]
    assert 'defName="OEC_Armor_M"]' in second


def test_kid_overrides_mass_bulk_and_drop_carry():
    from oe_ce.constants import BIOTECH_PACKAGE

    core = {
        "OE_Armor_Kid": CoreApparel("OE_Armor_Kid", ARMOR, None, BIOTECH_PACKAGE),
        "OE_Helmet_Kid": CoreApparel("OE_Helmet_Kid", HELMET, None, BIOTECH_PACKAGE),
    }
    armor = ApparelSet(
        "kid", "proto", [ApparelMember("OE_Armor_Kid", mass=18, bulk=50, worn_bulk=7)],
        may_require=BIOTECH_PACKAGE,
    )
    xml = emit_apparel_xml([armor], ARMOR, core)
    ET.fromstring(xml)
    assert "<ArmorRating_Sharp>16</ArmorRating_Sharp>" in xml
    assert "<Mass>18</Mass>" in xml
    assert "<Bulk>50</Bulk>" in xml
    assert "<WornBulk>7</WornBulk>" in xml
    assert "<Mass>30</Mass>" not in xml
    assert "CarryWeight" not in xml
    assert "CombatExtended.PartialArmorExt" in xml
    assert f'MayRequire="{BIOTECH_PACKAGE}"' in xml
    helmet = ApparelSet(
        "kid", "proto", [ApparelMember("OE_Helmet_Kid", mass=1.8, bulk=2.5)],
        may_require=BIOTECH_PACKAGE,
    )
    xml = emit_apparel_xml([helmet], HELMET, core)
    assert "<Mass>1.8</Mass>" in xml
    assert "<Bulk>2.5</Bulk>" in xml
    assert "<WornBulk>1</WornBulk>" in xml
