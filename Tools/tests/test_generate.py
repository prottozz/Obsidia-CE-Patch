from pathlib import Path
from oe_ce.generate import generate

ROOT = Path(__file__).resolve().parents[2]


def test_generate_cerberus_files(monkeypatch):
    monkeypatch.setenv("OE_CE_ALLOW_PARTIAL", "1")
    generate(ROOT)
    ammo = (ROOT / "Defs" / "Ammo" / "OE_Ammo.xml").read_text(encoding="utf-8")
    guns = (ROOT / "Patches" / "Weapons" / "OE_Ranged.xml").read_text(encoding="utf-8")
    assert "AmmoSet_OE_cerberus_ballistic" in ammo
    assert "OE_Rifle" in guns
    assert "OCC_Rifle" in guns
