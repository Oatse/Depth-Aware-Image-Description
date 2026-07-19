from typing import Final

import numpy as np

from services.depth_output import build_depth_summary, empty_depth_summary
from services.depth_types import NAVIGATION_PRIORITY, RegionStats


REGION_NAMES = (
    "upper_left",
    "upper_center",
    "upper_right",
    "middle_left",
    "middle_center",
    "middle_right",
    "lower_left",
    "lower_center",
    "lower_right",
)

VERY_CLOSE_THRESHOLD: Final = 1.0
CLOSE_THRESHOLD: Final = 1.6
FAR_THRESHOLD: Final = 2.4


def analyze_depth_regions(depth_map: np.ndarray | None) -> dict:
    if depth_map is None or depth_map.size == 0:
        return empty_depth_summary()

    regions = split_regions(depth_map)
    if not np.isfinite(depth_map).any():
        return empty_depth_summary()
    region_stats = {
        name: _calculate_region_stats(region)
        for name, region in regions.items()
    }
    nearest_region = _select_nearest_region(region_stats)
    safe_direction = _choose_safe_direction(region_stats)
    return build_depth_summary(
        nearest_region,
        region_stats,
        safe_direction,
    )


def split_regions(depth_map: np.ndarray) -> dict[str, np.ndarray]:
    if depth_map.ndim != 2:
        raise ValueError("Depth map must be a 2D array.")

    row_splits = np.array_split(depth_map, 3, axis=0)
    regions: dict[str, np.ndarray] = {}
    index = 0
    for row in row_splits:
        for column in np.array_split(row, 3, axis=1):
            regions[REGION_NAMES[index]] = column
            index += 1
    return regions


def categorize_distance(depth_score: float) -> str:
    if not np.isfinite(depth_score):
        return "tidak_diketahui"
    if depth_score < VERY_CLOSE_THRESHOLD:
        return "sangat_dekat"
    if depth_score < CLOSE_THRESHOLD:
        return "dekat"
    if depth_score < FAR_THRESHOLD:
        return "sedang"
    return "jauh"


def _calculate_region_stats(region: np.ndarray) -> RegionStats:
    finite = region[np.isfinite(region)]
    if finite.size == 0:
        infinity = float("inf")
        return RegionStats(
            "tidak_diketahui",
            infinity,
            infinity,
            infinity,
            infinity,
        )
    p10 = float(np.percentile(finite, 10))
    mean = float(np.mean(finite))
    median = float(np.median(finite))
    return RegionStats(
        category=categorize_distance(p10),
        score=p10,
        p10=p10,
        mean=mean,
        median=median,
    )


def _select_nearest_region(region_stats: dict[str, RegionStats]) -> str:
    priority_scores = [
        (name, region_stats[name].score)
        for name in NAVIGATION_PRIORITY
        if name in region_stats
    ]
    return min(priority_scores, key=lambda item: item[1])[0]


def _choose_safe_direction(region_stats: dict[str, RegionStats]) -> str:
    direction_scores = (
        ("kiri", min(region_stats["lower_left"].score, region_stats["middle_left"].score)),
        ("kanan", min(region_stats["lower_right"].score, region_stats["middle_right"].score)),
        ("tengah", min(region_stats["lower_center"].score, region_stats["middle_center"].score)),
    )
    best_direction, best_score = max(direction_scores, key=lambda item: item[1])
    return best_direction if np.isfinite(best_score) else "tidak_diketahui"
