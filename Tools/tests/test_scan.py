import os
from pathlib import Path

from oe_ce.constants import DEFAULT_OBSIDIA_CORE
from oe_ce.scan_obsidia import scan_core_ranged

CORE = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))


def test_scan_finds_proto_cerberus():
    names = scan_core_ranged(CORE)
    assert "OE_Rifle" in names
    assert "OCC_Rifle" in names
    assert "Bullet_OE_R" not in names
