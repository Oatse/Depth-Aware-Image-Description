from dataclasses import dataclass


NAVIGATION_PRIORITY = (
    "lower_center",
    "middle_center",
    "lower_left",
    "lower_right",
    "middle_left",
    "middle_right",
)


@dataclass(frozen=True, slots=True)
class RegionStats:
    category: str
    score: float
    p10: float
    mean: float
    median: float
