import numpy as np

from services.depth_analysis import analyze_depth_regions, categorize_distance, split_regions


def test_split_regions_returns_nine_named_regions() -> None:
    depth_map = np.arange(81, dtype=np.float32).reshape(9, 9)

    regions = split_regions(depth_map)

    assert len(regions) == 9
    assert regions["upper_left"].shape == (3, 3)
    assert regions["lower_right"].shape == (3, 3)


def test_categorize_distance_thresholds() -> None:
    assert categorize_distance(0.3) == "sangat_dekat"
    assert categorize_distance(0.7) == "dekat"
    assert categorize_distance(1.4) == "sedang"
    assert categorize_distance(2.4) == "jauh"


def test_analyze_depth_regions_prioritizes_nearest_front_region() -> None:
    depth_map = np.full((9, 9), 2.5, dtype=np.float32)
    depth_map[6:9, 3:6] = 0.4
    depth_map[3:6, 6:9] = 2.8
    depth_map[6:9, 6:9] = 2.8

    summary = analyze_depth_regions(depth_map)

    assert summary["nearest_region"] == "lower_center"
    assert summary["distance_category"] == "sangat_dekat"
    assert summary["front_area_status"] == "potensi_halangan"
    assert summary["safe_direction"] == "kanan"
