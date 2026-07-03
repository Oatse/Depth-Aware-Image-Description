from dataclasses import dataclass

import numpy as np


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

REGION_DISPLAY_NAMES = {
    "upper_left": "atas-kiri",
    "upper_center": "atas-tengah",
    "upper_right": "atas-kanan",
    "middle_left": "tengah-kiri",
    "middle_center": "tengah",
    "middle_right": "tengah-kanan",
    "lower_left": "bawah-kiri",
    "lower_center": "bawah-tengah",
    "lower_right": "bawah-kanan",
}

NAVIGATION_PRIORITY = (
    "lower_center",
    "middle_center",
    "lower_left",
    "lower_right",
    "middle_left",
    "middle_right",
)


@dataclass(frozen=True)
class RegionStats:
    category: str
    score: float
    p10: float
    mean: float
    median: float


def analyze_depth_regions(depth_map: np.ndarray | None) -> dict:
    if depth_map is None or depth_map.size == 0:
        return {
            "nearest_region": "tidak_diketahui",
            "distance_category": "tidak_diketahui",
            "warning": "Informasi kedalaman tidak tersedia.",
            "safe_direction": "tidak_diketahui",
            "regions": {},
        }

    regions = split_regions(depth_map)
    region_stats = {
        name: _calculate_region_stats(region)
        for name, region in regions.items()
    }
    nearest_region = _select_nearest_region(region_stats)
    nearest_stats = region_stats[nearest_region]
    safe_direction = _choose_safe_direction(region_stats)

    return {
        "nearest_region": nearest_region,
        "distance_category": nearest_stats.category,
        "estimated_distance": _estimated_distance_text(nearest_stats.category),
        "front_area_status": _front_area_status(nearest_stats.category),
        "warning": _warning_text(nearest_region, nearest_stats.category),
        "safe_direction": safe_direction,
        "regions": {
            name: {
                "category": stats.category,
                "score": round(stats.score, 4),
                "p10": round(stats.p10, 4),
                "mean": round(stats.mean, 4),
                "median": round(stats.median, 4),
            }
            for name, stats in region_stats.items()
        },
    }


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


def categorize_distance(distance_meter: float) -> str:
    if not np.isfinite(distance_meter):
        return "tidak_diketahui"
    if distance_meter < 0.5:
        return "sangat_dekat"
    if distance_meter < 1.0:
        return "dekat"
    if distance_meter < 2.0:
        return "sedang"
    return "jauh"


def _calculate_region_stats(region: np.ndarray) -> RegionStats:
    finite = region[np.isfinite(region)]
    if finite.size == 0:
        return RegionStats("tidak_diketahui", float("inf"), float("inf"), float("inf"), float("inf"))
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
    priority_scores = [(name, region_stats[name].score) for name in NAVIGATION_PRIORITY if name in region_stats]
    return min(priority_scores, key=lambda item: item[1])[0]


def _choose_safe_direction(region_stats: dict[str, RegionStats]) -> str:
    left_score = min(region_stats["lower_left"].score, region_stats["middle_left"].score)
    right_score = min(region_stats["lower_right"].score, region_stats["middle_right"].score)
    center_score = min(region_stats["lower_center"].score, region_stats["middle_center"].score)
    best_direction, best_score = max(
        (("kiri", left_score), ("kanan", right_score), ("tengah", center_score)),
        key=lambda item: item[1],
    )
    if not np.isfinite(best_score):
        return "tidak_diketahui"
    return best_direction


def _front_area_status(category: str) -> str:
    return "terhalang" if category in {"sangat_dekat", "dekat"} else "aman"


def _estimated_distance_text(category: str) -> str:
    return {
        "sangat_dekat": "kurang dari 0.5 meter",
        "dekat": "sekitar 0.5 sampai 1 meter",
        "sedang": "sekitar 1 sampai 2 meter",
        "jauh": "lebih dari 2 meter",
    }.get(category, "tidak diketahui")


def _warning_text(region_name: str, category: str) -> str:
    region_label = REGION_DISPLAY_NAMES.get(region_name, region_name)
    if category == "sangat_dekat":
        return f"Terdapat hambatan sangat dekat di area {region_label}."
    if category == "dekat":
        return f"Terdapat hambatan dekat di area {region_label}."
    if category == "sedang":
        return f"Area {region_label} memiliki objek pada jarak sedang."
    if category == "jauh":
        return "Area depan tampak relatif lapang berdasarkan estimasi kedalaman."
    return "Informasi kedalaman tidak cukup untuk memberi peringatan."
