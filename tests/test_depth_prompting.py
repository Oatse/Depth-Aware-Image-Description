from models.depth_prompting import build_depth_spatial_prompt


def test_build_depth_spatial_prompt_includes_relative_depth_metadata() -> None:
    prompt = build_depth_spatial_prompt({
        "nearest_region": "lower_center",
        "distance_category": "dekat",
        "safe_direction": "kanan",
        "front_area_status": "potensi_halangan",
    })

    assert "Depth-to-Spatial Prompting Schema" in prompt
    assert "lower_center" in prompt
    assert "dekat" in prompt
    assert "kanan" in prompt
    assert "potensi halangan visual" in prompt
    assert "bukan ukuran meter presisi" in prompt
