# Tools/tests/test_skeleton.py
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_loadfolders_does_not_load_tools_or_catalog():
    text = (ROOT / "LoadFolders.xml").read_text(encoding="utf-8")
    assert "Tools" not in text
    assert "catalog" not in text
    assert "<li>Defs</li>" in text
    assert "<li>Patches</li>" in text


def test_about_package_id():
    text = (ROOT / "About" / "About.xml").read_text(encoding="utf-8")
    assert "<packageId>prottozz.ObsidiaCEPatch</packageId>" in text
    assert "CETeam.CombatExtended" in text
    assert "ObsidiaExpansion.Core" in text
    assert "Ludeon.RimWorld.Royalty" in text
    assert "Ludeon.RimWorld.Anomaly" in text
    assert "Ludeon.RimWorld.Ideology" in text
    assert "Ludeon.RimWorld.Biotech" in text
    assert "Alias.DegeneralizeWork" in text
    assert "optionalDependencies" not in text
