from scripts.build_controlled_fusion_predictions import build_controlled_fusion_rows


def test_controlled_fusion_reuses_identical_semantic_and_depth_branches() -> None:
    # Given
    gemma_prediction = {
        "image_name": "sample.jpg",
        "mode": "gemma_only",
        "description_gemma": "Terlihat kursi di sisi kiri ruangan.",
        "main_object": "kursi",
        "object_position": "kiri",
        "scene_type": "indoor",
        "gemma_latency_ms": "100",
        "total_latency_ms": "110",
        "error": "",
    }
    depth_summary = {
        "nearest_region": "lower_right",
        "distance_category": "dekat",
        "estimated_distance": "dekat secara relatif",
        "safe_direction": "kiri",
        "warning": "Area bawah-kanan menunjukkan potensi halangan visual dekat.",
    }

    # When
    rows = build_controlled_fusion_rows(gemma_prediction, depth_summary, depth_latency_ms=20)

    # Then
    assert {row["mode"] for row in rows} == {
        "gemma_depth_legacy_controlled",
        "gemma_depth_constrained_controlled",
    }
    assert {row["main_object"] for row in rows} == {"kursi"}
    assert {row["object_position"] for row in rows} == {"kiri"}
    assert {row["nearest_region"] for row in rows} == {"lower_right"}
    assert {row["distance_category"] for row in rows} == {"dekat"}
    assert {row["source_modes"] for row in rows} == {"gemma_only+shared_depth"}
    assert "Region kiri terbaca relatif lebih lapang" in rows[0]["final_description"]
    assert "Region kiri terbaca relatif lebih lapang" not in rows[1]["final_description"]


def test_controlled_fusion_rejects_failed_gemma_branch() -> None:
    # Given
    gemma_prediction = {
        "image_name": "sample.jpg",
        "mode": "gemma_only",
        "description_gemma": "",
        "main_object": "",
        "object_position": "",
        "scene_type": "",
        "gemma_latency_ms": "0",
        "total_latency_ms": "0",
        "error": "Gemma failed",
    }

    # When / Then
    try:
        build_controlled_fusion_rows(gemma_prediction, {}, depth_latency_ms=20)
    except ValueError as exc:
        assert "successful gemma_only" in str(exc)
    else:
        raise AssertionError("failed Gemma branch must be rejected")
