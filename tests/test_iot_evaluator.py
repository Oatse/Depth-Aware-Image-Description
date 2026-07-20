import csv

import pytest

from services.evaluator import evaluate_iot_manifest


FIELDS = [
    "capture_id", "status", "ground_truth_cm", "sensor_1_cm", "sensor_2_cm", "timestamp_offset_ms",
    "mode", "total_latency_ms", "gemma_depth_latency_ms", "sensor_depth_consistent",
    "iot_description_score", "gemma_depth_description_score",
]


def _write_manifest(path):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow({"capture_id": "a", "status": "paired", "ground_truth_cm": "80", "sensor_1_cm": "81", "sensor_2_cm": "83", "timestamp_offset_ms": "10", "mode": "iot_assisted", "total_latency_ms": "220", "gemma_depth_latency_ms": "200", "sensor_depth_consistent": "yes", "iot_description_score": "4", "gemma_depth_description_score": "3"})
        writer.writerow({"capture_id": "b", "status": "pair_conflict", "ground_truth_cm": "40", "sensor_1_cm": "20", "sensor_2_cm": "90", "timestamp_offset_ms": "20", "mode": "iot_assisted", "total_latency_ms": "240", "gemma_depth_latency_ms": "200", "sensor_depth_consistent": "no", "iot_description_score": "3", "gemma_depth_description_score": "3"})


def test_iot_metrics_separate_pairing_and_quality(tmp_path) -> None:
    manifest = tmp_path / "manifest.csv"
    _write_manifest(manifest)
    summary = evaluate_iot_manifest(manifest)
    assert summary.capture_count == 2
    assert summary.pairing_coverage == 0.5
    assert summary.conflict_rate == 0.5
    assert summary.absolute_error_cm == 2.0
    assert summary.latency_overhead_ms == 30.0
    assert summary.description_quality_delta == 0.5


def test_iot_manifest_requires_measured_ground_truth(tmp_path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("capture_id,status\na,paired\n", encoding="utf-8")
    with pytest.raises(ValueError, match="columns missing"):
        evaluate_iot_manifest(manifest)
