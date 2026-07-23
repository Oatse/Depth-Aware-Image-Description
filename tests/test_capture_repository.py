import pytest

from services.capture_repository import (
    CaptureAlreadyExistsError,
    CaptureRepository,
    CaptureRepositoryError,
    CaptureStateError,
)


def _create(repository: CaptureRepository, capture_id: str = "cap-001") -> dict:
    return repository.create(
        image_bytes=b"image-bytes",
        original_filename="camera.jpg",
        content_type="image/jpeg",
        width=40,
        height=32,
        capture_id=capture_id,
        batch_id="batch-001",
        capture_time_ms=1_000_000,
        camera_facing_mode="environment",
        mode="sensor_assisted",
        sensor_evidence={"capture_id": capture_id, "status": "paired", "samples": {}},
        metadata={"camera_sensor_offset_cm": 3.0},
    )


def test_capture_repository_persists_image_record_and_count(tmp_path) -> None:
    repository = CaptureRepository(tmp_path / "captures")

    record = _create(repository)

    assert record["status"] == "captured"
    assert repository.read_image("cap-001") == b"image-bytes"
    assert repository.count(batch_id="batch-001") == 1
    assert repository.list(batch_id="batch-001")[0]["sensor_evidence"]["status"] == "paired"
    assert (tmp_path / "captures" / "records" / "cap-001.json").is_file()
    assert (tmp_path / "captures" / "images" / "cap-001.jpg").is_file()


def test_capture_repository_can_store_clean_dataset_prefix(tmp_path) -> None:
    repository = CaptureRepository(tmp_path / "captures")

    record = repository.create(
        image_bytes=b"clean-image",
        original_filename="camera.jpg",
        content_type="image/jpeg",
        width=40,
        height=32,
        capture_id="cap-clean",
        batch_id="batch-clean",
        capture_time_ms=1,
        camera_facing_mode="environment",
        mode="sensor_assisted",
        sensor_evidence=None,
        metadata={"ground_truth_cm": 50.0, "target_id": "koper-hitam-01", "repeat_index": 1},
        image_path_prefix="images/dataset_v3_clean",
    )

    assert record["image"]["path"] == "images/dataset_v3_clean/cap-clean.jpg"
    assert repository.read_image("cap-clean") == b"clean-image"


def test_capture_repository_assigns_repeat_index_per_batch_distance_and_target(tmp_path) -> None:
    repository = CaptureRepository(tmp_path / "captures")

    first = repository.create(
        image_bytes=b"first",
        original_filename="first.jpg",
        content_type="image/jpeg",
        width=40,
        height=32,
        capture_id="cap-001",
        batch_id="batch-001",
        capture_time_ms=1,
        camera_facing_mode="environment",
        mode="sensor_assisted",
        sensor_evidence=None,
        metadata={"ground_truth_cm": 30.0, "target_id": "planar", "repeat_index": None},
    )
    second = repository.create(
        image_bytes=b"second",
        original_filename="second.jpg",
        content_type="image/jpeg",
        width=40,
        height=32,
        capture_id="cap-002",
        batch_id="batch-001",
        capture_time_ms=2,
        camera_facing_mode="environment",
        mode="sensor_assisted",
        sensor_evidence=None,
        metadata={"ground_truth_cm": 30.0, "target_id": "planar", "repeat_index": None},
    )

    assert first["metadata"]["repeat_index"] == 1
    assert second["metadata"]["repeat_index"] == 2


def test_clean_dataset_allows_a_fourth_repeat(tmp_path) -> None:
    repository = CaptureRepository(tmp_path / "captures")
    for repeat in (1, 2, 3):
        repository.create(
            image_bytes=f"image-{repeat}".encode(),
            original_filename="camera.jpg",
            content_type="image/jpeg",
            width=40,
            height=32,
            capture_id=f"clean-{repeat}",
            batch_id="default",
            capture_time_ms=repeat,
            camera_facing_mode="environment",
            mode="sensor_assisted",
            sensor_evidence=None,
            metadata={"ground_truth_cm": 50.0, "target_id": None, "repeat_index": None},
            image_path_prefix="images/dataset_v2_clean",
        )

    fourth = repository.create(
        image_bytes=b"image-4",
        original_filename="camera.jpg",
        content_type="image/jpeg",
        width=40,
        height=32,
        capture_id="clean-4",
        batch_id="default",
        capture_time_ms=4,
        camera_facing_mode="environment",
        mode="sensor_assisted",
        sensor_evidence=None,
        metadata={"ground_truth_cm": 50.0, "target_id": None, "repeat_index": None},
        image_path_prefix="images/dataset_v2_clean",
    )
    assert fourth["metadata"]["repeat_index"] == 4


def test_capture_repository_never_overwrites_an_existing_capture(tmp_path) -> None:
    repository = CaptureRepository(tmp_path / "captures")
    _create(repository)

    with pytest.raises(CaptureAlreadyExistsError):
        _create(repository)


def test_capture_repository_enforces_one_analysis_lifecycle(tmp_path) -> None:
    repository = CaptureRepository(tmp_path / "captures")
    _create(repository)

    queued = repository.mark_queued("cap-001", job_id="job-001", mode="sensor_assisted")
    assert queued["status"] == "queued"
    assert repository.mark_running("cap-001")["status"] == "running"
    completed = repository.mark_completed("cap-001", analysis_run_id="run-001")
    assert completed["status"] == "completed"
    assert completed["analysis_run_id"] == "run-001"

    with pytest.raises(CaptureStateError, match="sudah selesai"):
        repository.mark_queued("cap-001", job_id="job-002", mode="sensor_assisted")


def test_capture_repository_recovers_a_job_orphaned_by_backend_restart(tmp_path) -> None:
    repository = CaptureRepository(tmp_path / "captures")
    _create(repository)
    repository.mark_queued("cap-001", job_id="lost-job", mode="sensor_assisted")

    recovered = repository.recover_orphaned_analysis("cap-001")
    retried = repository.mark_queued("cap-001", job_id="job-002", mode="sensor_assisted")

    assert recovered["status"] == "failed"
    assert "backend restart" in recovered["analysis_error"]
    assert retried["status"] == "queued"
    assert retried["analysis_attempts"] == 2
