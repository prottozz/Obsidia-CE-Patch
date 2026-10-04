from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from oe_ce.constants import DEFAULT_OBSIDIA_CORE
from oe_ce.load import load_catalog
from oe_ce.scan_obsidia import scan_core_ranged
from oe_ce.validate import validate_catalog


def main() -> int:
    core = Path(os.environ.get("OBSIDIA_CORE", DEFAULT_OBSIDIA_CORE))
    cat = load_catalog(ROOT / "catalog")
    errs = validate_catalog(cat, scan_core_ranged(core))
    for e in errs:
        print(e)
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
