from pathlib import Path
import xml.etree.ElementTree as ET

from oe_ce.emit_races import collect_race_tools, convert_tool_element, emit_race_xml
from oe_ce.race_analogues import ANIMAL, MECHANOID
from oe_ce.race_models import RaceMember, RaceSet, RaceTool
from oe_ce.scan_races import CoreRace

BIOTECH_PACKAGE = "Ludeon.RimWorld.Biotech"
ANOMALY_PACKAGE = "Ludeon.RimWorld.Anomaly"
IDEOLOGY_PACKAGE = "Ludeon.RimWorld.Ideology"
ROYALTY_PACKAGE = "Ludeon.RimWorld.Royalty"

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
    scanned = {
        **CORE,
        "OE_Mech_ChaosLord": CoreRace("OE_Mech_ChaosLord", MECHANOID),
    }
    xml = emit_race_xml(
        [
            RaceSet(
                "chaos_lord",
                "diabolus",
                "Humanoid",
                [RaceMember("OE_Mech_ChaosLord")],
                may_require=BIOTECH_PACKAGE,
            )
        ],
        MECHANOID,
        scanned,
        {},
    )
    assert 'MayRequire="Ludeon.RimWorld.Biotech"' in xml
    assert "<ArmorRating_Sharp>24</ArmorRating_Sharp>" in xml
    assert "<ArmorRating_Blunt>54</ArmorRating_Blunt>" in xml
    assert "<bodyShape>Humanoid</bodyShape>" in xml
    root = ET.fromstring(xml.split("?>", 1)[1])
    outer = next(op for op in root if op.get("MayRequire") == "Ludeon.RimWorld.Biotech")
    assert outer.get("Class") == "PatchOperationConditional"
    seq = outer.find("match")
    assert seq is not None and seq.get("Class") == "PatchOperationSequence"
    ops = seq.find("operations")
    assert ops is not None
    children = list(ops)
    assert children
    for child in children:
        assert child.tag == "li", child.tag
        assert child.get("Class")


def test_maid_walker_is_wrapped_biotech():
    scanned = {**CORE, "OE_Mech_Maid": CoreRace("OE_Mech_Maid", MECHANOID)}
    xml = emit_race_xml(
        [RaceSet("maid", "walker", "Humanoid", [RaceMember("OE_Mech_Maid")], may_require=BIOTECH_PACKAGE)],
        MECHANOID,
        scanned,
        {},
    )
    assert "<ArmorRating_Sharp>4</ArmorRating_Sharp>" in xml
    assert "<bodyShape>Humanoid</bodyShape>" in xml
    assert f'MayRequire="{BIOTECH_PACKAGE}"' in xml
    inner = xml.split("<operations>")[1].split("</operations>")[0]
    assert "<li Class=" in inner
    assert "<Operation Class=" not in inner


def test_invincible_slime_is_wrapped_anomaly():
    scanned = {**CORE, "OE_ChaosSlime_Invincible": CoreRace("OE_ChaosSlime_Invincible", ANIMAL)}
    xml = emit_race_xml(
        [
            RaceSet(
                "chaos_slime",
                "hide",
                "QuadrupedLow",
                [
                    RaceMember(
                        "OE_ChaosSlime_Invincible",
                        analogue="thrumbo",
                        body_shape="QuadrupedTall",
                    )
                ],
                may_require=ANOMALY_PACKAGE,
            )
        ],
        ANIMAL,
        scanned,
        {},
    )
    assert "<ArmorRating_Sharp>14</ArmorRating_Sharp>" in xml
    assert "<bodyShape>QuadrupedTall</bodyShape>" in xml
    assert f'MayRequire="{ANOMALY_PACKAGE}"' in xml


def test_dryad_is_wrapped_ideology():
    scanned = {**CORE, "OE_Dryad_Synthesis": CoreRace("OE_Dryad_Synthesis", ANIMAL)}
    xml = emit_race_xml(
        [RaceSet("dryad", "hide", members=[RaceMember("OE_Dryad_Synthesis")], may_require=IDEOLOGY_PACKAGE)],
        ANIMAL,
        scanned,
        {},
    )
    assert "<ArmorRating_Sharp>0.05</ArmorRating_Sharp>" in xml
    assert f'MayRequire="{IDEOLOGY_PACKAGE}"' in xml


def test_hidden_entity_unhides_stats_inside_anomaly_wrap():
    scanned = {
        **CORE,
        "OE_CyberArachna": CoreRace("OE_CyberArachna", ANIMAL, hide_stats=True),
    }
    xml = emit_race_xml(
        [
            RaceSet(
                "cyber_arachna",
                "megaspider",
                "QuadrupedLow",
                [RaceMember("OE_CyberArachna")],
                may_require=ANOMALY_PACKAGE,
            )
        ],
        ANIMAL,
        scanned,
        {},
    )
    assert "<hideStats>false</hideStats>" in xml
    assert f'MayRequire="{ANOMALY_PACKAGE}"' in xml
    assert xml.index("<hideStats>false</hideStats>") > xml.index(f'MayRequire="{ANOMALY_PACKAGE}"')


def test_luraxin_is_wrapped_royalty():
    scanned = {**CORE, "OE_Slime_Luraxin": CoreRace("OE_Slime_Luraxin", ANIMAL)}
    xml = emit_race_xml(
        [
            RaceSet(
                "slime_soft",
                "hide",
                "QuadrupedLow",
                [RaceMember("OE_Slime_Luraxin", may_require=ROYALTY_PACKAGE)],
            )
        ],
        ANIMAL,
        scanned,
        {},
    )
    assert "<ArmorRating_Sharp>0.05</ArmorRating_Sharp>" in xml
    assert f'MayRequire="{ROYALTY_PACKAGE}"' in xml


def test_core_only_emit_omits_unscanned_optional_members():
    xml = emit_race_xml(
        [RaceSet("maid", "walker", "Humanoid", [RaceMember("OE_Mech_Maid")], may_require=BIOTECH_PACKAGE)],
        MECHANOID,
        CORE,
        {},
    )
    assert "OE_Mech_Maid" not in xml


def _write_races(root: Path, body: str) -> Path:
    races = root / "Defs" / "ThingDefs_Races"
    races.mkdir(parents=True, exist_ok=True)
    (races / "Fixture.xml").write_text(
        f'<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n{body}\n</Defs>\n',
        encoding="utf-8",
    )
    return root


def _emitted_tools(xml: str, def_name: str) -> list[ET.Element]:
    root = ET.fromstring(xml.split("?>", 1)[1])
    found: list[ET.Element] = []
    for op in root:
        if (op.findtext("xpath") or "") != f'Defs/ThingDef[defName="{def_name}"]/tools':
            continue
        for branch in (op.find("match"), op.find("nomatch")):
            if branch is None:
                continue
            tools = branch.find("value/tools")
            if tools is not None:
                found.append(tools)
    return found


INHERITED_TOOLS_FIXTURE = """
  <ThingDef Name="OEBaseBeast" Abstract="True">
    <tools>
      <li>
        <label>left claw</label>
        <capacities><li>Scratch</li></capacities>
        <power>12</power>
        <cooldownTime>2</cooldownTime>
        <armorPenetration>0.30</armorPenetration>
      </li>
    </tools>
  </ThingDef>
  <ThingDef ParentName="OEBaseBeast">
    <defName>OE_Direwolf</defName>
    <race />
  </ThingDef>
  <ThingDef Name="OEBaseArachna" Abstract="True">
    <tools>
      <li>
        <label>left claw</label>
        <capacities><li>Scratch</li></capacities>
        <armorPenetration>0.20</armorPenetration>
      </li>
      <li>
        <label>right claw</label>
        <capacities><li>Scratch</li></capacities>
        <armorPenetration>0.20</armorPenetration>
      </li>
      <li>
        <label>head</label>
        <capacities><li>Blunt</li></capacities>
        <armorPenetration>0.10</armorPenetration>
      </li>
    </tools>
  </ThingDef>
  <ThingDef ParentName="OEBaseArachna">
    <defName>OE_Arachna_Blue</defName>
    <race />
    <tools>
      <li>
        <label>bite</label>
        <capacities><li>Bite</li></capacities>
        <armorPenetration>0.28</armorPenetration>
      </li>
    </tools>
  </ThingDef>
"""


def test_inherited_tools_emit_inherit_false_and_all_parent_attacks(tmp_path):
    core = _write_races(tmp_path, INHERITED_TOOLS_FIXTURE)
    tools = collect_race_tools(core)
    xml = emit_race_xml(
        [
            RaceSet("direwolf", "warg", members=[RaceMember("OE_Direwolf")]),
            RaceSet("arachna", "megaspider", members=[RaceMember("OE_Arachna_Blue")]),
        ],
        ANIMAL,
        {
            "OE_Direwolf": CoreRace("OE_Direwolf", ANIMAL),
            "OE_Arachna_Blue": CoreRace("OE_Arachna_Blue", ANIMAL),
        },
        tools,
    )
    wolf = _emitted_tools(xml, "OE_Direwolf")
    assert wolf
    for block in wolf:
        assert block.get("Inherit") == "False"
        lis = list(block)
        assert len(lis) == 1
        assert all(li.get("Class") == "CombatExtended.ToolCE" for li in lis)
        assert lis[0].findtext("label") == "left claw"
        assert lis[0].find("armorPenetration") is None
        assert lis[0].find("armorPenetrationSharp") is not None

    arachna = _emitted_tools(xml, "OE_Arachna_Blue")
    assert arachna
    for block in arachna:
        assert block.get("Inherit") == "False"
        lis = list(block)
        assert len(lis) == 4
        assert all(li.get("Class") == "CombatExtended.ToolCE" for li in lis)
        labels = [li.findtext("label") for li in lis]
        assert "bite" in labels
        assert labels.count("left claw") == 1
        assert labels.count("right claw") == 1
        assert labels.count("head") == 1
        assert all(li.find("armorPenetration") is None for li in lis)


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


def test_collect_race_tools_reads_anomaly_tree(tmp_path):
    core = tmp_path / "core"
    (core / "Defs" / "ThingDefs_Races").mkdir(parents=True)
    (core / "Defs" / "ThingDefs_Races" / "Core.xml").write_text(
        '<?xml version="1.0"?><Defs><ThingDef><defName>OE_Direwolf</defName><race /></ThingDef></Defs>',
        encoding="utf-8",
    )
    anomaly = tmp_path / "anomaly"
    (anomaly / "Defs" / "ThingDefs_Races").mkdir(parents=True)
    (anomaly / "Defs" / "ThingDefs_Races" / "A.xml").write_text(
        """<?xml version="1.0"?>
<Defs>
  <ThingDef>
    <defName>OE_Returned</defName>
    <race />
    <tools>
      <li>
        <label>claw</label>
        <capacities><li>Scratch</li></capacities>
        <power>8</power>
        <cooldownTime>2</cooldownTime>
        <armorPenetration>0.2</armorPenetration>
      </li>
    </tools>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    tools = collect_race_tools(core, anomaly=anomaly)
    assert tools["OE_Returned"][0].armor_penetration_sharp == 0.2
