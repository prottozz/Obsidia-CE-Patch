from pathlib import Path

import pytest

from oe_ce.scan_bodies import scan_bodies

CORE_FIXTURE = """
  <BodyDef Name="OEBaseBlob" Abstract="True">
    <corePart><def>Body</def></corePart>
  </BodyDef>
  <BodyDef>
    <defName>OESlimeLike</defName>
    <corePart>
      <def>Body</def>
      <parts>
        <li>
          <def>Stomach</def>
          <coverage>0.05</coverage>
          <depth>Inside</depth>
        </li>
        <li>
          <def>Eye</def>
          <coverage>0.05</coverage>
        </li>
      </parts>
    </corePart>
  </BodyDef>
"""

BIO_FIXTURE = """
  <BodyDef>
    <defName>OEMechanicalOcto</defName>
    <corePart><def>OEOctoHood</def></corePart>
  </BodyDef>
"""

ANOMALY_FIXTURE = """
  <BodyDef>
    <defName>OEReturnedLike</defName>
    <corePart>
      <def>Torso</def>
      <groups><li>Torso</li></groups>
    </corePart>
  </BodyDef>
"""

VANILLA_FIXTURE = """
  <BodyDef>
    <defName>Lancer</defName>
    <corePart><def>MechanicalThorax</def></corePart>
  </BodyDef>
"""


def _write_bodies(root: Path, body: str) -> Path:
    dest = root / "Defs" / "Bodies"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "Fixture.xml").write_text(
        f'<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n{body}\n</Defs>\n',
        encoding="utf-8",
    )
    return root


def test_scan_skips_abstracts_and_vanilla(tmp_path):
    core = _write_bodies(tmp_path, CORE_FIXTURE + VANILLA_FIXTURE)
    found = scan_bodies(core)
    assert set(found) == {"OESlimeLike"}
    assert found["OESlimeLike"].custom is True
    slime = found["OESlimeLike"]
    assert slime.parts[0].xpath == "corePart"
    assert slime.parts[0].children[0].def_name == "Stomach"
    assert slime.parts[0].children[0].depth == "Inside"
    assert slime.parts[0].children[1].depth is None


def test_scan_fails_without_bodies_dir(tmp_path):
    with pytest.raises(FileNotFoundError, match="bodies"):
        scan_bodies(tmp_path)


def test_biotech_and_anomaly_optional(tmp_path):
    core = _write_bodies(tmp_path / "core", CORE_FIXTURE)
    bio = _write_bodies(tmp_path / "bio", BIO_FIXTURE)
    anomaly = _write_bodies(tmp_path / "anomaly", ANOMALY_FIXTURE)
    found = scan_bodies(core, bio, anomaly)
    assert "OEMechanicalOcto" in found
    assert "OEReturnedLike" in found
    assert found["OEReturnedLike"].parts[0].groups == ("Torso",)


def test_core_only_omits_dlc(tmp_path):
    core = _write_bodies(tmp_path, CORE_FIXTURE)
    found = scan_bodies(core, tmp_path / "nope")
    assert "OEMechanicalOcto" not in found
    assert "OESlimeLike" in found
