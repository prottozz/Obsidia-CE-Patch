import xml.etree.ElementTree as ET

from oe_ce.emit_races import convert_tool_element, emit_race_xml
from oe_ce.race_analogues import ANIMAL, MECHANOID
from oe_ce.race_models import RaceMember, RaceSet, RaceTool
from oe_ce.scan_races import CoreRace

CORE = {
    "OE_Direwolf": CoreRace("OE_Direwolf", ANIMAL),
    "OE_Direwolf_Pup": CoreRace("OE_Direwolf_Pup", ANIMAL, "OE_Direwolf"),
    "OE_Mech_DarkCrusader": CoreRace("OE_Mech_DarkCrusader", MECHANOID),
    "OE_Mech_OCC_Dominator": CoreRace("OE_Mech_OCC_Dominator", MECHANOID),
}

CLAW = RaceTool(
    label="left claw",
    capacities=("Scratch",),
    linked_body_parts_group="FrontLeftPaw",
    power=12,
    cooldown_time=2,
    armor_penetration_sharp=0.30,
)


def test_convert_scratch_uses_sharp_blunt_uses_blunt():
    scratch = ET.fromstring(
        "<li><label>left claw</label><capacities><li>Scratch</li></capacities>"
        "<armorPenetration>0.30</armorPenetration></li>"
    )
    blunt = ET.fromstring(
        "<li><label>left fist</label><capacities><li>Blunt</li></capacities>"
        "<armorPenetration>0.5</armorPenetration>"
        "<alwaysTreatAsWeapon>true</alwaysTreatAsWeapon></li>"
    )
    s = convert_tool_element(scratch)
    b = convert_tool_element(blunt)
    assert s.armor_penetration_sharp == 0.30
    assert s.armor_penetration_blunt is None
    assert b.armor_penetration_blunt == 0.5
    assert b.armor_penetration_sharp is None
    assert any("alwaysTreatAsWeapon" in x for x in b.extra_xml)


def test_direwolf_gets_warg_shape_stats_toolce_and_animal_durability():
    xml = emit_race_xml(
        [RaceSet("direwolf", "warg", members=[RaceMember("OE_Direwolf", tools=[CLAW])])],
        ANIMAL,
        CORE,
        {},
    )
    assert "<bodyShape>Quadruped</bodyShape>" in xml
    assert "<ArmorRating_Sharp>0.1</ArmorRating_Sharp>" in xml
    assert 'Class="CombatExtended.ToolCE"' in xml
    assert "<armorPenetrationSharp>0.3</armorPenetrationSharp>" in xml
    assert "CompProperties_ArmorDurability" in xml
    assert "<RegenInterval>600</RegenInterval>" in xml
    assert "Repairable" not in xml
    assert "MoveSpeed" not in xml
    assert "ArmorRating_Heat" not in xml


def test_dark_crusader_is_centipede_humanoid_without_ammo_giver():
    xml = emit_race_xml(
        [RaceSet("crusader", "centipede", "Humanoid", [RaceMember("OE_Mech_DarkCrusader")])],
        MECHANOID,
        CORE,
        {},
    )
    assert "<ArmorRating_Sharp>20</ArmorRating_Sharp>" in xml
    assert "<bodyShape>Humanoid</bodyShape>" in xml
    assert "CompAmmoGiver" not in xml
    assert "<Repairable>true</Repairable>" in xml
    assert "<RegenInterval>1250</RegenInterval>" in xml
    assert "<ArmorRating_Heat>0.25</ArmorRating_Heat>" in xml


def test_child_of_catalogued_parent_gets_stats_but_no_second_extension():
    s = RaceSet(
        "direwolf",
        "warg",
        members=[RaceMember("OE_Direwolf"), RaceMember("OE_Direwolf_Pup")],
    )
    xml = emit_race_xml([s], ANIMAL, CORE, {})
    assert xml.count("PatchOperationAddModExtension") == 1
    assert '<xpath>Defs/ThingDef[defName="OE_Direwolf"]</xpath>' in xml
    assert (
        '<xpath>Defs/ThingDef[defName="OE_Direwolf_Pup"]/statBases/ArmorRating_Sharp</xpath>'
        in xml
    )
    assert xml.count("CompProperties_ArmorDurability") == 1


def test_biotech_boss_is_wrapped_with_mayrequire():
    xml = emit_race_xml(
        [RaceSet("chaos_lord", "diabolus", "Humanoid", [RaceMember("OE_Mech_ChaosLord")])],
        MECHANOID,
        CORE,
        {},
    )
    assert 'MayRequire="Ludeon.RimWorld.Biotech"' in xml
    assert "<ArmorRating_Sharp>24</ArmorRating_Sharp>" in xml
    assert "<ArmorRating_Blunt>54</ArmorRating_Blunt>" in xml
    assert "<bodyShape>Humanoid</bodyShape>" in xml


def test_kind_filter_and_sorted_patch():
    sets = [
        RaceSet("crusader", "centipede", "Humanoid", [RaceMember("OE_Mech_DarkCrusader")]),
        RaceSet(
            "dom",
            "walker",
            members=[RaceMember("OE_Mech_OCC_Dominator"), RaceMember("OE_Direwolf")],
        ),
    ]
    xml = emit_race_xml(sets, MECHANOID, CORE, {})
    root = ET.fromstring(xml.split("?>", 1)[1])
    assert root.tag == "Patch"
    assert "OE_Direwolf" not in xml
    assert xml.index('defName="OE_Mech_DarkCrusader"') < xml.index('defName="OE_Mech_OCC_Dominator"')
