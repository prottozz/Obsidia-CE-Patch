from pathlib import Path

from oe_ce.emit_guns import emit_gun_patches
from oe_ce.models import Family, Member


def _minimal_core(tmp_path: Path, *, with_tools: bool) -> Path:
    weapons = tmp_path / "Defs" / "ThingDefs_Misc" / "Weapons"
    weapons.mkdir(parents=True)
    tools_block = "    <tools><li /></tools>\n" if with_tools else ""
    (weapons / "Guns.xml").write_text(
        f"""<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef>
    <defName>OE_Rifle</defName>
    <verbs><li /></verbs>
{tools_block}  </ThingDef>
  <ThingDef>
    <defName>OCC_Rifle</defName>
    <verbs><li /></verbs>
{tools_block}  </ThingDef>
</Defs>
""",
        encoding="utf-8",
    )
    return tmp_path


def test_shared_ammoset_different_stats(tmp_path):
    fam = Family(
        "cerberus",
        "rifle",
        "ballistic",
        members=[
            Member("OE_Rifle", "proto"),
            Member("OCC_Rifle", "occ"),
        ],
    )
    core = _minimal_core(tmp_path, with_tools=True)
    xml = emit_gun_patches([fam], core)
    assert xml.count("AmmoSet_OE_cerberus_ballistic") == 2
    assert "<defName>OE_Rifle</defName>" in xml
    assert "<defName>OCC_Rifle</defName>" in xml
    assert "PatchOperationMakeGunCECompatible" in xml
    assert "<range>55</range>" in xml
    assert "<range>48</range>" in xml
    assert "PatchOperationReplace" in xml


def test_tools_replace_skipped_without_core_tools(tmp_path):
    fam = Family(
        "cerberus",
        "rifle",
        "ballistic",
        members=[Member("OE_Rifle", "proto")],
    )
    core = _minimal_core(tmp_path, with_tools=False)
    xml = emit_gun_patches([fam], core)
    assert "PatchOperationReplace" not in xml
