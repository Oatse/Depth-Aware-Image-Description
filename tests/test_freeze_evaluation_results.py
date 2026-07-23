import csv
import json
from pathlib import Path

import pytest

from scripts.freeze_evaluation_results import (
    build_evaluation_manifest,
    validate_evaluation_manifest,
)


def _write_fixture(root: Path) -> None:
    captures_root = root / "results" / "captures"
    records_root = captures_root / "records"
    records_root.mkdir(parents=True)
    capture_id = "capture-1"
    run_id = "run-1"
    dataset = {
        "dataset_id": "dataset-v2",
        "batch_id": "batch-v2",
        "captures": [{
            "capture_id": capture_id,
            "ground_truth_cm": 30.0,
            "repeat_index": 1,
            "image_sha256": "image-hash",
            "input_sha256": "input-hash",
            "sensor_1_cm": 26.5,
            "sensor_2_cm": 26.7,
        }],
    }
    (captures_root / "dataset_manifest_v2.json").write_text(
        json.dumps(dataset), encoding="utf-8"
    )
    (records_root / f"{capture_id}.json").write_text(json.dumps({
        "capture_id": capture_id,
        "status": "completed",
        "analysis_attempts": 1,
        "analysis_run_id": run_id,
    }), encoding="utf-8")
    run = {
        "analysis_run_id": run_id,
        "capture_id": capture_id,
        "sensor_evidence": {
            "capture_id": capture_id,
            "samples": {
                "sensor_1": {"distance_cm": 26.5},
                "sensor_2": {"distance_cm": 26.7},
            },
        },
        "outputs": {
            "sensor_assisted": {
                "success": True,
                "mode": "sensor_assisted",
                "mock": {"gemma": False},
                "gemma_description": "Deskripsi visual.",
                "gemma_structured": {"main_object": "objek"},
                "final_description": "Deskripsi visual. Referensi sensor.",
                "sensor_contribution": {
                    "calibration_version": "cal-v1",
                },
                "latency": {"gemma_ms": 10, "total_ms": 12},
            }
        },
    }
    (root / "results" / "analysis_runs.jsonl").write_text(
        json.dumps(run) + "\n", encoding="utf-8"
    )
    with (captures_root / "dataset_analysis_rows_v2.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as output_file:
        writer = csv.DictWriter(output_file, fieldnames=["capture_id", "analysis_run_id"])
        writer.writeheader()
        writer.writerow({"capture_id": capture_id, "analysis_run_id": run_id})
    with (captures_root / "dataset_visual_scores_v2.csv").open(
        "w", encoding="utf-8", newline=""
    ) as output_file:
        writer = csv.DictWriter(output_file, fieldnames=["capture_id", "clarity"])
        writer.writeheader()
        writer.writerow({"capture_id": capture_id, "clarity": 4})


def test_evaluation_manifest_freezes_and_validates_selected_run(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    manifest = build_evaluation_manifest(
        tmp_path,
        evaluation_id="evaluation-v2",
        model_id="google/gemma-4-e2b",
        artifact_paths=("results/captures/dataset_manifest_v2.json",),
        expected_capture_count=1,
    )
    result = validate_evaluation_manifest(
        tmp_path,
        manifest,
        expected_capture_count=1,
    )

    assert manifest["total_captures"] == 1
    assert manifest["captures"][0]["analysis_run_id"] == "run-1"
    assert manifest["model"]["raw_provider_response_preserved"] is False
    assert result["run_checksums_verified"] == 1
    assert result["sensor_snapshots_verified"] == 1


def test_evaluation_manifest_rejects_modified_artifact(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    manifest = build_evaluation_manifest(
        tmp_path,
        evaluation_id="evaluation-v2",
        model_id="google/gemma-4-e2b",
        artifact_paths=("results/captures/dataset_manifest_v2.json",),
        expected_capture_count=1,
    )
    (tmp_path / "results/captures/dataset_manifest_v2.json").write_text(
        "{}", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Checksum artefak tidak cocok"):
        validate_evaluation_manifest(tmp_path, manifest, expected_capture_count=1)
