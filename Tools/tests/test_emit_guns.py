from oe_ce.emit_guns import emit_gun_patches
from oe_ce.models import Family, Member


def test_shared_ammoset_different_stats():
    fam = Family(
        "cerberus",
        "rifle",
        "ballistic",
        members=[
            Member("OE_Rifle", "proto"),
            Member("OCC_Rifle", "occ"),
        ],
    )
    xml = emit_gun_patches([fam])
    assert xml.count("AmmoSet_OE_cerberus_ballistic") == 2
    assert "<defName>OE_Rifle</defName>" in xml
    assert "<defName>OCC_Rifle</defName>" in xml
    assert "PatchOperationMakeGunCECompatible" in xml
    assert "<range>55</range>" in xml
    assert "<range>48</range>" in xml
