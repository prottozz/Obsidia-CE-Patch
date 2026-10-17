import os
from pathlib import Path

import pytest

from oe_ce.constants import DEFAULT_OBSIDIA_BIOTECH, DEFAULT_OBSIDIA_CORE
from oe_ce.race_analogues import ANIMAL, MECHANOID
from oe_ce.scan_races import BIOTECH_BOSSES, scan_races

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


def test_biotech_only_four_bosses(tmp_path):
    core = _write_races(tmp_path / "core", FIXTURE)
    bio = _write_races(tmp_path / "bio", BIO_FIXTURE)
    found = scan_races(core, bio)
    assert BIOTECH_BOSSES <= set(found)
    assert "OE_Mech_ArachnaDrone" not in found
    assert found["OE_Mech_ChaosLord"].kind == MECHANOID


def test_biotech_missing_is_core_only(tmp_path):
    core = _write_races(tmp_path, FIXTURE)
    found = scan_races(core, tmp_path / "nope")
    assert "OE_Mech_ChaosLord" not in found
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
    assert BIOTECH_BOSSES <= set(found)
    assert found["OE_Mech_CrimsonArachna"].kind == MECHANOID
