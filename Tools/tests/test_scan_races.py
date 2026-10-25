import os
from pathlib import Path

import pytest

from oe_ce.constants import DEFAULT_OBSIDIA_BIOTECH, DEFAULT_OBSIDIA_CORE
from oe_ce.race_analogues import ANIMAL, MECHANOID
from oe_ce.scan_races import scan_races

CORE = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))
BIOTECH = Path(os.environ.get("OBSIDIA_BIOTECH", DEFAULT_OBSIDIA_BIOTECH))

FIXTURE = """
  <ThingDef Name="OEBaseBeast" Abstract="True">
    <race><fleshType>Insectoid</fleshType></race>
  </ThingDef>
  <ThingDef ParentName="OEBaseBeast">
    <defName>OE_Armagon</defName>
  </ThingDef>
  <ThingDef>
    <defName>OE_Direwolf</defName>
    <race />
  </ThingDef>
  <ThingDef>
    <defName>OE_Mech_OCC_Dominator</defName>
    <race><fleshType>Mechanoid</fleshType></race>
  </ThingDef>
  <ThingDef>
    <defName>Bullet_Bruul_Acid</defName>
  </ThingDef>
  <PawnKindDef>
    <defName>OE_DirewolfKind</defName>
  </PawnKindDef>
"""

BIO_FIXTURE = """
  <ThingDef>
    <defName>OE_Mech_ChaosLord</defName>
    <race />
  </ThingDef>
  <ThingDef>
    <defName>OE_Mech_ArachnaQueen</defName>
    <race />
  </ThingDef>
  <ThingDef>
    <defName>OE_Mech_CrimsonArachna</defName>
    <race />
  </ThingDef>
  <ThingDef>
    <defName>OE_Mech_FallenLegion</defName>
    <race />
  </ThingDef>
  <ThingDef>
    <defName>OE_Mech_ArachnaDrone</defName>
    <race />
  </ThingDef>
"""

ANOMALY_FIXTURE = """
  <ThingDef Name="OEBaseChaosSlime" ParentName="BasePawn" Abstract="True">
    <race><fleshType>Fleshbeast</fleshType></race>
  </ThingDef>
  <ThingDef ParentName="OEBaseChaosSlime">
    <defName>OE_ChaosSlime_Larval</defName>
  </ThingDef>
  <ThingDef>
    <defName>OE_CyberArachna</defName>
    <hideStats>true</hideStats>
    <race><fleshType>EntityFlesh</fleshType></race>
  </ThingDef>
"""

IDEOLOGY_FIXTURE = """
  <ThingDef ParentName="DryadBase">
    <defName>OE_Dryad_Synthesis</defName>
    <race />
  </ThingDef>
  <ThingDef Name="OE_AwakenedDryad_Synthesis" Abstract="True">
    <race />
  </ThingDef>
"""

ROYALTY_FIXTURE = """
  <ThingDef Name="OEBaseLiquidSlime" Abstract="True">
    <race><fleshType>Flesh</fleshType></race>
  </ThingDef>
  <ThingDef ParentName="OEBaseLiquidSlime">
    <defName>OE_Slime_Luraxin</defName>
  </ThingDef>
"""


def _write_races(root: Path, body: str) -> Path:
    races = root / "Defs" / "ThingDefs_Races"
    races.mkdir(parents=True, exist_ok=True)
    (races / "Fixture.xml").write_text(
        f'<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n{body}\n</Defs>\n',
        encoding="utf-8",
    )
    return root


def test_scan_classifies_and_skips_bullets_and_pawnkinds(tmp_path):
    core = _write_races(tmp_path, FIXTURE)
    found = scan_races(core)
    assert set(found) == {"OE_Armagon", "OE_Direwolf", "OE_Mech_OCC_Dominator"}
    assert found["OE_Armagon"].kind == ANIMAL
    assert found["OE_Direwolf"].kind == ANIMAL
    assert found["OE_Mech_OCC_Dominator"].kind == MECHANOID
    assert "Bullet_Bruul_Acid" not in found


def test_scan_fails_without_races_dir(tmp_path):
    with pytest.raises(FileNotFoundError, match="races"):
        scan_races(tmp_path)


def test_biotech_scans_all_races_not_only_bosses(tmp_path):
    core = _write_races(tmp_path / "core", FIXTURE)
    bio = _write_races(tmp_path / "bio", BIO_FIXTURE)
    found = scan_races(core, bio)
    assert "OE_Mech_ChaosLord" in found
    assert "OE_Mech_ArachnaDrone" in found
    assert found["OE_Mech_ArachnaDrone"].kind == MECHANOID


def test_anomaly_entities_are_animals(tmp_path):
    core = _write_races(tmp_path / "core", FIXTURE)
    anomaly = _write_races(tmp_path / "anomaly", ANOMALY_FIXTURE)
    found = scan_races(core, anomaly=anomaly)
    assert found["OE_ChaosSlime_Larval"].kind == ANIMAL
    assert found["OE_CyberArachna"].kind == ANIMAL
    assert found["OE_CyberArachna"].hide_stats is True
    assert found["OE_ChaosSlime_Larval"].hide_stats is False


def test_ideology_dryad_scanned_abstract_skipped(tmp_path):
    core = _write_races(tmp_path / "core", FIXTURE)
    ideo = _write_races(tmp_path / "ideo", IDEOLOGY_FIXTURE)
    found = scan_races(core, ideology=ideo)
    assert "OE_Dryad_Synthesis" in found
    assert "OE_AwakenedDryad_Synthesis" not in found


BIO_INHERITED_RACE_FIXTURE = """
  <ThingDef ParentName="OEBaseBeast">
    <defName>OE_Scorpid_Tox</defName>
  </ThingDef>
"""


def test_biotech_race_inherited_from_core_parent(tmp_path):
    core = _write_races(tmp_path / "core", FIXTURE)
    bio = _write_races(tmp_path / "bio", BIO_INHERITED_RACE_FIXTURE)
    found = scan_races(core, bio)
    assert "OE_Scorpid_Tox" in found
    assert found["OE_Scorpid_Tox"].kind == ANIMAL


def test_biotech_missing_is_core_only(tmp_path):
    core = _write_races(tmp_path, FIXTURE)
    found = scan_races(core, tmp_path / "nope")
    assert "OE_Mech_ChaosLord" not in found
    assert "OE_Direwolf" in found


def test_royalty_slime_scanned_when_royalty_passed(tmp_path):
    core = _write_races(tmp_path / "core", FIXTURE)
    roy = _write_races(tmp_path / "roy", ROYALTY_FIXTURE)
    found = scan_races(core, royalty=roy)
    assert "OE_Slime_Luraxin" in found
    assert found["OE_Slime_Luraxin"].kind == ANIMAL


def test_royalty_missing_is_core_only(tmp_path):
    core = _write_races(tmp_path, FIXTURE)
    found = scan_races(core)
    assert "OE_Slime_Luraxin" not in found
    assert "OE_Direwolf" in found


def test_real_core_race_counts():
    found = scan_races(CORE)
    animals = {n for n, r in found.items() if r.kind == ANIMAL}
    mechs = {n for n, r in found.items() if r.kind == MECHANOID}
    assert len(animals) == 57
    assert len(mechs) == 21
    assert "OE_Armagon" in animals
    assert "Bullet_Bruul_Acid" not in found
    assert "OE_Mech_CAC_Arachna" in mechs
    assert "OE_Mech_CrimsonArachna" not in found


def test_real_biotech_bosses_when_present():
    if not (BIOTECH / "Defs" / "ThingDefs_Races").is_dir():
        pytest.skip("Obsidia Biotech races dir not installed")
    found = scan_races(CORE, BIOTECH)
    assert "OE_Mech_CrimsonArachna" in found
    assert "OE_Mech_Maid" in found
    assert found["OE_Mech_CrimsonArachna"].kind == MECHANOID
