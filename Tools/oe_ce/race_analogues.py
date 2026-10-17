from __future__ import annotations

from dataclasses import dataclass

ANIMAL = "animal"
MECHANOID = "mechanoid"

BODY_SHAPES = frozenset(
    {
        "Humanoid",
        "HumanoidWide",
        "Quadruped",
        "QuadrupedLow",
        "QuadrupedTall",
        "Serpentine",
        "Birdlike",
    }
)


@dataclass(frozen=True)
class RaceStats:
    body_shape: str
    sharp: float
    blunt: float
    heat: float | None
    dodge: float
    crit: float
    parry: float
    durability: int


def _row(
    body_shape: str,
    sharp: float,
    blunt: float,
    heat: float | None,
    dodge: float,
    crit: float,
    parry: float,
    durability: int,
) -> RaceStats:
    return RaceStats(body_shape, sharp, blunt, heat, dodge, crit, parry, durability)


ANALOGUES: dict[str, RaceStats] = {
    "hide": _row("Quadruped", 0.05, 0.075, None, 0.16, 0.14, 0.10, 400),
    "warg": _row("Quadruped", 0.10, 0.15, None, 0.23, 0.20, 0.11, 700),
    "cougar": _row("Quadruped", 0.10, 0.15, None, 0.22, 0.18, 0.10, 575),
    "megascarab": _row("QuadrupedLow", 0.70, 2.25, None, 0.08, 0.12, 0.10, 150),
    "megaspider": _row("QuadrupedLow", 4, 10, None, 0.10, 0.20, 0.15, 925),
    "thrumbo": _row("QuadrupedTall", 14, 21, 0.60, 0.10, 0.82, 0.48, 3000),
    "walker": _row("Humanoid", 4, 6, 0, 0.13, 0.12, 0.09, 800),
    "pikeman": _row("Quadruped", 7, 15, 0, 0.04, 0.13, 0.15, 1200),
    "centipede": _row("QuadrupedLow", 20, 45, 0.25, 0.03, 0.26, 0.52, 3660),
    "diabolus": _row("QuadrupedLow", 24, 54, 0.50, 0.03, 0.42, 0.64, 4250),
    "warqueen": _row("QuadrupedLow", 24, 54, 0.50, 0.02, 0.22, 0.64, 4600),
    "warqueen_plus": _row("QuadrupedLow", 26, 58, 0.50, 0.02, 0.22, 0.64, 5000),
    "apocriton": _row("Humanoid", 24, 60, 0.50, 0.07, 0.13, 0.13, 3100),
    "apocriton_plus": _row("Humanoid", 26, 64, 0.50, 0.07, 0.13, 0.13, 3400),
}


def race_stats(analogue: str) -> RaceStats:
    return ANALOGUES[analogue]
