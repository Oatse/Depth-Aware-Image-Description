from services.depth_types import RegionStats


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


def empty_depth_summary() -> dict:
    return {
        "analysis_method": "grid_p10",
        "nearest_region": "tidak_diketahui",
        "distance_category": "tidak_diketahui",
        "warning": "Informasi kedalaman tidak tersedia.",
        "safe_direction": "tidak_diketahui",
        "regions": {},
    }


def build_depth_summary(
    nearest_region: str,
    region_stats: dict[str, RegionStats],
    safe_direction: str,
) -> dict:
    nearest_stats = region_stats[nearest_region]
    return {
        "analysis_method": "grid_p10",
        "nearest_region": nearest_region,
        "distance_category": nearest_stats.category,
        "estimated_distance": _estimated_distance_text(nearest_stats.category),
        "front_area_status": _front_area_status(nearest_stats.category),
        "warning": _warning_text(nearest_region, nearest_stats.category),
        "safe_direction": safe_direction,
        "regions": {
            name: _serialize_region(stats)
            for name, stats in region_stats.items()
        },
    }


def _serialize_region(stats: RegionStats) -> dict[str, object]:
    return {
        "category": stats.category,
        "score": round(stats.score, 4),
        "p10": round(stats.p10, 4),
        "mean": round(stats.mean, 4),
        "median": round(stats.median, 4),
    }


def _front_area_status(category: str) -> str:
    return "potensi_halangan" if category in {"sangat_dekat", "dekat"} else "relatif_lapang"


def _estimated_distance_text(category: str) -> str:
    return {
        "sangat_dekat": "sangat dekat secara relatif",
        "dekat": "dekat secara relatif",
        "sedang": "sedang secara relatif",
        "jauh": "jauh secara relatif",
    }.get(category, "tidak diketahui")


def _warning_text(region_name: str, category: str) -> str:
    region_label = REGION_DISPLAY_NAMES.get(region_name, region_name)
    if category == "sangat_dekat":
        return f"Area {region_label} menunjukkan potensi halangan visual sangat dekat."
    if category == "dekat":
        return f"Area {region_label} menunjukkan potensi halangan visual dekat."
    if category == "sedang":
        return f"Area {region_label} memiliki objek pada jarak sedang."
    if category == "jauh":
        return "Area depan tampak relatif lapang berdasarkan estimasi kedalaman."
    return "Informasi kedalaman tidak cukup untuk memberi peringatan."
