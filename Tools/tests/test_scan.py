from pathlib import Path

from oe_ce.scan_obsidia import scan_core_ranged

CORE = Path(r"C:\Projects\Assistant\294100\2519492373\1.6\Core")


def test_scan_finds_proto_cerberus():
    names = scan_core_ranged(CORE)
    assert "OE_Rifle" in names
    assert "OCC_Rifle" in names
    assert "Bullet_OE_R" not in names
