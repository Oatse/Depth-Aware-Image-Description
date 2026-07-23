import json
from pathlib import Path

import pytest

from scripts.freeze_capture_dataset import build_manifest, validate_manifest


def _write_capture(
    root: Path,
    *,
    distance: float,
    repeat: int,
    capture_id: str | None = None,
    batch_id: str = "batch-1",
) -> None:
    capture_id = capture_id or f"capture-{distance:g}-{repeat}"
    image_relative_path = f"images/{capture_id}.jpg"
    image_path = root / image_relative_path
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(f"image-{capture_id}".encode())
    record = {
        "capture_id": capture_id,
        "batch_id": batch_id,
        "capture_time_ms": repeat,
        "camera_facing_mode": "environment",
        "mode": "sensor_assisted",
        "image": {"path": image_relative_path},
        "sensor_evidence": {
            "status": "paired",
            "samples": {
                "sensor_1": {"distance_cm": distance - 3.1, "status": "ok"},
                "sensor_2": {"distance_cm": distance - 2.9, "status": "ok"},
            },
            "pair_disagreement_cm": 0.2,
        },
        "metadata": {
            "camera_sensor_offset_cm": 3.0,
            "ground_truth_cm": distance,
            "sensor_face_ground_truth_cm": distance - 3.0,
            "target_id": None,
            "repeat_index": repeat,
        },
    }
    records_dir = root / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    (records_dir / f"{capture_id}.json").write_text(json.dumps(record), encoding="utf-8")


def test_build_manifest_freezes_complete_distance_repeat_grid(tmp_path: Path) -> None:
    for distance in (30.0, 50.0, 75.0, 100.0, 150.0, 200.0):
        for repeat in (1, 2, 3):
            _write_capture(tmp_path, distance=distance, repeat=repeat)

    manifest = build_manifest(tmp_path, dataset_id="test-v1")

    assert manifest["dataset_id"] == "test-v1"
    assert manifest["total_captures"] == 18
    assert manifest["captures"][0]["ground_truth_cm"] == 30.0
    assert manifest["captures"][-1]["ground_truth_cm"] == 200.0
    assert all(len(row["image_sha256"]) == 64 for row in manifest["captures"])
    assert all(len(row["input_sha256"]) == 64 for row in manifest["captures"])
    assert all(row["sensor_1_status"] == "ok" for row in manifest["captures"])
    assert all(row["sensor_2_status"] == "ok" for row in manifest["captures"])
    assert validate_manifest(tmp_path, manifest)["checksums_verified"] == 18


def test_build_manifest_rejects_missing_distance(tmp_path: Path) -> None:
    for distance in (30.0, 50.0, 75.0, 100.0, 150.0, 200.0):
        for repeat in (1, 2, 3):
            if distance != 200.0:
                _write_capture(tmp_path, distance=distance, repeat=repeat)

    with pytest.raises(ValueError, match="Jarak yang hilang"):
        build_manifest(tmp_path, dataset_id="test-v1")


def test_build_manifest_allows_more_than_three_repeats(tmp_path: Path) -> None:
    for distance in (30.0, 50.0, 75.0, 100.0, 150.0, 200.0):
        for repeat in (1, 2, 3):
            _write_capture(tmp_path, distance=distance, repeat=repeat)
    _write_capture(tmp_path, distance=50.0, repeat=4, capture_id="capture-50-4")

    manifest = build_manifest(tmp_path, dataset_id="test-v2")

    assert manifest["total_captures"] == 19
    assert manifest["expected_repeats_per_distance"] is None
    assert manifest["repeat_counts_by_distance"]["50"] == 4
    assert validate_manifest(tmp_path, manifest)["repeat_counts_by_distance"]["50"] == 4


def test_build_manifest_filters_one_dataset_batch(tmp_path: Path) -> None:
    for distance in (30.0, 50.0, 75.0, 100.0, 150.0, 200.0):
        for repeat in (1, 2, 3):
            _write_capture(tmp_path, distance=distance, repeat=repeat)
    for path in (tmp_path / "records").glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["batch_id"] = "dataset-v2"
        path.write_text(json.dumps(record), encoding="utf-8")

    manifest = build_manifest(tmp_path, dataset_id="test-v2", batch_id="dataset-v2")

    assert manifest["batch_id"] == "dataset-v2"
    assert manifest["total_captures"] == 18


def test_validate_manifest_rejects_modified_image(tmp_path: Path) -> None:
    for distance in (30.0, 50.0, 75.0, 100.0, 150.0, 200.0):
        for repeat in (1, 2, 3):
            _write_capture(tmp_path, distance=distance, repeat=repeat)
    manifest = build_manifest(tmp_path, dataset_id="test-v2")
    (tmp_path / manifest["captures"][0]["image_path"]).write_bytes(b"modified")

    with pytest.raises(ValueError, match="Checksum gambar tidak cocok"):
        validate_manifest(tmp_path, manifest)


def test_validate_manifest_ignores_analysis_mode_changes(tmp_path: Path) -> None:
    for distance in (30.0, 50.0, 75.0, 100.0, 150.0, 200.0):
        for repeat in (1, 2, 3):
            _write_capture(tmp_path, distance=distance, repeat=repeat)
    manifest = build_manifest(tmp_path, dataset_id="test-v2")
    record_path = tmp_path / "records" / "capture-30-1.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["mode"] = "gemma_only"
    record["analysis_attempts"] = 3
    record["analysis_run_id"] = "new-analysis-run"
    record_path.write_text(json.dumps(record), encoding="utf-8")

    assert validate_manifest(tmp_path, manifest)["checksums_verified"] == 18


def test_build_manifest_can_select_ids_and_copy_to_clean_prefix(tmp_path: Path) -> None:
    for distance in (30.0, 50.0, 75.0, 100.0, 150.0, 200.0):
        for repeat in (1, 2, 3):
            _write_capture(tmp_path, distance=distance, repeat=repeat)

    capture_ids = {
        f"capture-{distance:g}-{repeat}"
        for distance in (30.0, 50.0, 75.0, 100.0, 150.0, 200.0)
        for repeat in (1, 2, 3)
    }
    manifest = build_manifest(
        tmp_path,
        dataset_id="test-v3",
        capture_ids=capture_ids,
        image_output_prefix="images/dataset_v3_clean",
    )

    assert manifest["image_path_prefix"] == "images/dataset_v3_clean"
    assert all(row["image_path"].startswith("images/dataset_v3_clean/") for row in manifest["captures"])
    assert validate_manifest(tmp_path, manifest)["checksums_verified"] == 18


def test_build_manifest_merges_old_rows_with_50_and_75_replacements(tmp_path: Path) -> None:
    selected_ids: set[str] = set()
    for distance in (30.0, 50.0, 75.0, 100.0, 150.0, 200.0):
        for repeat in (1, 2, 3):
            old_id = f"capture-{distance:g}-{repeat}"
            _write_capture(tmp_path, distance=distance, repeat=repeat, capture_id=old_id)
            if distance not in {50.0, 75.0}:
                selected_ids.add(old_id)
    for distance in (50.0, 75.0):
        for repeat in (1, 2, 3):
            replacement_id = f"replacement-{distance:g}-{repeat}"
            _write_capture(
                tmp_path,
                distance=distance,
                repeat=repeat,
                capture_id=replacement_id,
                batch_id="default",
            )
            selected_ids.add(replacement_id)

    manifest = build_manifest(
        tmp_path,
        dataset_id="hcsr04-indoor-distance-v2-clean",
        capture_ids=selected_ids,
    )

    replacement_rows = [
        row for row in manifest["captures"] if row["ground_truth_cm"] in {50.0, 75.0}
    ]
    assert len(replacement_rows) == 6
    assert all(row["capture_id"].startswith("replacement-") for row in replacement_rows)
    assert validate_manifest(tmp_path, manifest)["checksums_verified"] == 18
