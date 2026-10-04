from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from oe_ce.generate import generate


def main() -> None:
    generate(ROOT)


if __name__ == "__main__":
    main()
