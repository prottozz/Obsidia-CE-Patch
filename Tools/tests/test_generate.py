import shutil
from pathlib import Path

import pytest

from oe_ce.generate import generate

ROOT = Path(__file__).resolve().parents[2]


def _write_minimal_core(core: Path) -> None:
    weapons = core / "Defs" / "ThingDefs_Misc" / "Weapons"
    weapons.mkdir(parents=True)
    (weapons / "Rifles.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef>
    <defName>OE_Rifle</defName>
    <verbs><li /></verbs>
    <tools><li /></tools>
    <weaponTags><li>OE_ProtoGun</li></weaponTags>
  </ThingDef>
  <ThingDef>
    <defName>OCC_Rifle</defName>
    <verbs><li /></verbs>
    <tools><li /></tools>
    <weaponTags><li>OE_OccGun</li></weaponTags>
  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    pawnkinds = core / "Defs" / "PawnKinds"
    pawnkinds.mkdir(parents=True)


def test_generate_cerberus_files(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "fake_core"
    _write_minimal_core(core)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    monkeypatch.setenv("OE_CE_ALLOW_PARTIAL", "1")
    generate(tmp_path)
    ammo = (tmp_path / "Defs" / "Ammo" / "OE_Ammo.xml").read_text(encoding="utf-8")
    guns = (tmp_path / "Patches" / "Weapons" / "OE_Ranged.xml").read_text(encoding="utf-8")
    assert "Ammo_OE_rifle_ballistic_standard" in ammo
    assert "AmmoSet_OE_OE_Rifle" in ammo
    assert "OE_Rifle" in guns
    assert "OCC_Rifle" in guns


def test_generate_fails_without_core_weapons(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "catalog", tmp_path / "catalog")
    core = tmp_path / "empty_core"
    core.mkdir()
    (core / "Defs" / "PawnKinds").mkdir(parents=True)
    monkeypatch.setenv("OBSIDIA_CORE", str(core))
    with pytest.raises(FileNotFoundError, match="weapons"):
        generate(tmp_path)
