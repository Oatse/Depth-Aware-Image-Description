import json
from pathlib import Path

from scripts.summarize_capture_analysis import build_summary


def test_build_summary_uses_sensor_face_for_raw_and_camera_for_corrected_error(
    tmp_path: Path,
) -> None:
    captures_root = tmp_path / "captures"
    records_dir = captures_root / "records"
    records_dir.mkdir(parents=True)
    capture_id = "capture-1"
    run_id = "run-1"
    (records_dir / f"{capture_id}.json").write_text(
        json.dumps({
            "capture_id": capture_id,
            "status": "completed",
            "analysis_run_id": run_id,
        }),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({
            "schema_version": 2,
            "dataset_id": "test-v1",
            "captures": [{
                "capture_id": capture_id,
                "ground_truth_cm": 50.0,
                "sensor_face_ground_truth_cm": 47.0,
                "repeat_index": 1,
                "sensor_status": "paired",
                "sensor_1_cm": 46.5,
                "sensor_2_cm": 47.5,
                "image_sha256": "image-hash",
                "input_sha256": "input-hash",
            }],
        }),
        encoding="utf-8",
    )
    runs_path = tmp_path / "runs.jsonl"
    runs_path.write_text(
        json.dumps({
            "analysis_run_id": run_id,
            "capture_id": capture_id,
            "sensor_evidence": {"capture_id": capture_id},
            "outputs": {
                "sensor_assisted": {
                    "success": True,
                    "gemma_description": "Deskripsi visual.",
                    "final_description": "Deskripsi visual. Referensi sensor.",
                    "latency": {"gemma_ms": 10, "total_ms": 12},
                    "sensor_contribution": {
                        "status": "applied",
                        "sensor_1_cm": 46.5,
                        "sensor_2_cm": 47.5,
                        "sensor_1_corrected_cm": 49.5,
                        "sensor_2_corrected_cm": 50.5,
                        "frontal_reference_cm": 50.0,
                        "pair_disagreement_cm": 1.0,
                        "calibration_version": "cal-v1",
                    },
                }
            },
        }) + "\n",
        encoding="utf-8",
    )

    rows, summary = build_summary(captures_root, manifest_path, runs_path)

    assert rows[0]["sensor_1_raw_error_cm"] == -0.5
    assert rows[0]["sensor_2_raw_error_cm"] == 0.5
    assert rows[0]["sensor_1_corrected_error_cm"] == -0.5
    assert rows[0]["sensor_2_corrected_error_cm"] == 0.5
    assert rows[0]["frontal_error_cm"] == 0.0
    assert summary["overall"]["frontal_error"]["mae_cm"] == 0.0
