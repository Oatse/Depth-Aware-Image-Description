from scripts.build_fresh_dataset_reports import (
    ANALYSIS_FIELDS,
    VISUAL_FIELDS,
    _error_metrics,
    build_blinded_visual_rows,
)


def _analysis_row(
    *,
    capture_id: str,
    mode: str,
    run_id: str,
) -> dict[str, object]:
    return {
        "capture_id": capture_id,
        "ground_truth_cm": 50.0,
        "repeat_index": 1,
        "image_path": f"images/dataset_v2_clean/{capture_id}.jpg",
        "image_sha256": "a" * 64,
        "mode": mode,
        "model_id": "model",
        "analysis_run_id": run_id,
        "prompt_kind": "default_visual",
        "main_object": "objek",
        "closest_object": "objek",
        "object_position": "tengah",
        "gemma_description": "Sebuah objek tampak di tengah.",
    }


def test_core_fields_do_not_expose_target_specific_labels() -> None:
    forbidden = {
        "koper_in_main_object",
        "koper_in_description",
        "koper_label_present",
        "automatic_evaluation_note",
    }

    assert forbidden.isdisjoint(ANALYSIS_FIELDS)
    assert forbidden.isdisjoint(VISUAL_FIELDS)


def test_visual_rows_are_deterministic_and_hide_mode_provenance() -> None:
    rows = [
        _analysis_row(capture_id="capture-a", mode="gemma_only", run_id="run-a"),
        _analysis_row(
            capture_id="capture-a",
            mode="sensor_assisted",
            run_id="run-b",
        ),
    ]

    visual_rows, key_rows = build_blinded_visual_rows(rows, dataset_id="dataset")
    repeated_visual_rows, repeated_key_rows = build_blinded_visual_rows(
        rows,
        dataset_id="dataset",
    )

    assert visual_rows == repeated_visual_rows
    assert key_rows == repeated_key_rows
    assert {row["evaluation_item_id"] for row in visual_rows} == {
        row["evaluation_item_id"] for row in key_rows
    }
    assert all(
        {
            "capture_id",
            "ground_truth_cm",
            "repeat_index",
            "mode",
            "model_id",
            "analysis_run_id",
            "prompt_kind",
        }.isdisjoint(row)
        for row in visual_rows
    )
    assert all(
        str(row["image_path"]).startswith("images/visual_evaluation_blind_v2/VE-")
        and "capture-a" not in str(row["image_path"])
        for row in visual_rows
    )
    assert {row["mode"] for row in key_rows} == {
        "gemma_only",
        "sensor_assisted",
    }
    assert all(row["source_image_path"] for row in key_rows)


def test_error_metrics_report_bias_mae_and_rmse() -> None:
    assert _error_metrics([-1.0, 1.0]) == {
        "n": 2,
        "bias_cm": 0.0,
        "mae_cm": 1.0,
        "rmse_cm": 1.0,
        "max_abs_error_cm": 1.0,
    }
