# Tools/tests/test_skeleton.py
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_loadfolders_does_not_load_tools_or_catalog():
    text = (ROOT / "LoadFolders.xml").read_text(encoding="utf-8")
    assert "Tools" not in text
    assert "catalog" not in text
    assert "<v1.7>" in text
    assert "<li>1.7</li>" in text
    assert "<v1.6>" not in text


def test_generated_xml_lives_under_version_folder():
    assert (ROOT / "1.7" / "Defs" / "Ammo" / "OE_Ammo.xml").is_file()
    assert (ROOT / "1.7" / "Patches" / "Apparel" / "OE_Armor.xml").is_file()
    assert not (ROOT / "Defs").exists()
    assert not (ROOT / "Patches").exists()


def test_about_package_id():
    text = (ROOT / "About" / "About.xml").read_text(encoding="utf-8")
    assert "<packageId>prottozz.ObsidiaCEPatch</packageId>" in text
    assert "CETeam.CombatExtended" in text
    assert "ObsidiaExpansion.Core" in text
    assert "Ludeon.RimWorld.Royalty" in text
    assert "Ludeon.RimWorld.Anomaly" in text
    assert "Ludeon.RimWorld.Ideology" in text
    assert "Ludeon.RimWorld.Biotech" in text
    assert "Ludeon.RimWorld.Odyssey" in text
    assert "Alias.DegeneralizeWork" in text
    assert "optionalDependencies" not in text


def test_about_targets_1_7_only():
    text = (ROOT / "About" / "About.xml").read_text(encoding="utf-8")
    assert "<li>1.7</li>" in text
    assert "<li>1.6</li>" not in text
