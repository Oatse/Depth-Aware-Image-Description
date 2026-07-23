import io
import time

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from models.gemma_client import GemmaResult
from services.capture_repository import (
    CAPTURE_CANDIDATE_BATCH_ID,
    CAPTURE_CANDIDATE_IMAGE_PREFIX,
    CaptureRepository,
    incoming_capture_root,
)


def _sample_image_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (40, 32), color=(120, 140, 160)).save(buffer, format="JPEG")
    return buffer.getvalue()


class RecordingGemmaClient:
    def __init__(self) -> None:
        self.calls = 0

    async def describe_image(self, base64_image: str, prompt: str | None = None) -> GemmaResult:
        self.calls += 1
        return GemmaResult(
            "Satu target terlihat di tengah ruangan.",
            "{}",
            5,
            mock=True,
            structured={
                "scene_type": "indoor",
                "main_object": "target",
                "object_position": "tengah",
                "objects": ["target"],
                "obstacle_candidate": "tidak_diketahui",
                "description": "Satu target terlihat di tengah ruangan.",
            },
        )


class RecordingSensorBridge:
    def snapshot(self, capture_time_ms: int, window_ms: int) -> dict:
        return {
            "enabled": True,
            "connected": True,
            "capture_time_ms": capture_time_ms,
            "window_ms": window_ms,
            "status": "paired",
            "samples": {
                "sensor_1": {"distance_cm": 47.0, "age_ms": 4, "status": "ok"},
                "sensor_2": {"distance_cm": 47.2, "age_ms": 6, "status": "ok"},
            },
        }


class UnpairedSensorBridge:
    def snapshot(self, capture_time_ms: int, window_ms: int) -> dict:
        return {
            "enabled": True,
            "connected": True,
            "capture_time_ms": capture_time_ms,
            "window_ms": window_ms,
            "status": "partial",
            "samples": {
                "sensor_1": {"distance_cm": 47.0, "age_ms": 4, "status": "ok"},
            },
        }


def _create_capture(client: TestClient, capture_id: str = "cap-001"):
    capture_time_ms = int(time.time() * 1000)
    return client.post(
        "/captures",
        files={"image": ("camera.jpg", _sample_image_bytes(), "image/jpeg")},
        data={
            "capture_id": capture_id,
            "capture_time_ms": str(capture_time_ms),
            "camera_facing_mode": "environment",
            "mode": "sensor_assisted",
            "ground_truth_cm": "50",
            "repeat_index": "1",
            "image_path_prefix": "images/dataset_v2_clean",
        },
    )


def test_capture_rejects_missing_ground_truth(monkeypatch, tmp_path) -> None:
    import app.routes.analyze as analyze_route

    monkeypatch.setattr(analyze_route.settings, "results_dir", tmp_path)
    with TestClient(app) as client:
        app.state.sensor_bridge = RecordingSensorBridge()
        response = client.post(
            "/captures",
            files={"image": ("camera.jpg", _sample_image_bytes(), "image/jpeg")},
            data={
                "capture_id": "cap-without-ground-truth",
                "batch_id": "batch-clean-v2",
                "capture_time_ms": str(int(time.time() * 1000)),
                "camera_facing_mode": "environment",
                "mode": "sensor_assisted",
            },
        )

    assert response.status_code == 422
    assert not (incoming_capture_root(tmp_path) / "records").exists()


def test_capture_is_persisted_with_sensor_metadata_without_running_gemma(monkeypatch, tmp_path) -> None:
    import app.routes.analyze as analyze_route

    gemma = RecordingGemmaClient()
    monkeypatch.setattr(analyze_route.settings, "results_dir", tmp_path)
    monkeypatch.setattr(analyze_route, "gemma_client", gemma)
    with TestClient(app) as client:
        app.state.sensor_bridge = RecordingSensorBridge()
        response = _create_capture(client)
        count = client.get("/captures/count", params={"batch_id": CAPTURE_CANDIDATE_BATCH_ID})
        listing = client.get("/captures", params={"batch_id": CAPTURE_CANDIDATE_BATCH_ID})

    assert response.status_code == 201
    payload = response.json()
    capture = payload["capture"]
    assert gemma.calls == 0
    assert payload["capture_count"] == 1
    assert capture["status"] == "captured"
    assert capture["sensor_evidence"]["capture_id"] == "cap-001"
    assert capture["sensor_evidence"]["status"] == "paired"
    assert capture["metadata"]["ground_truth_cm"] == 50.0
    assert capture["metadata"]["sensor_face_ground_truth_cm"] == 47.0
    assert capture["metadata"]["repeat_index"] == 1
    assert capture["batch_id"] == CAPTURE_CANDIDATE_BATCH_ID
    assert count.json() == {"count": 1, "batch_id": CAPTURE_CANDIDATE_BATCH_ID}
    assert listing.json()["captures"][0]["capture_id"] == "cap-001"
    assert (
        incoming_capture_root(tmp_path)
        / CAPTURE_CANDIDATE_IMAGE_PREFIX
        / "cap-001.jpg"
    ).is_file()
    assert not (tmp_path / "captures" / "images" / "dataset_v2_clean").exists()


def test_candidate_capture_rejects_unpaired_sensor_snapshot(monkeypatch, tmp_path) -> None:
    import app.routes.analyze as analyze_route

    monkeypatch.setattr(analyze_route.settings, "results_dir", tmp_path)
    with TestClient(app) as client:
        app.state.sensor_bridge = UnpairedSensorBridge()
        response = client.post(
            "/captures",
            files={"image": ("camera.jpg", _sample_image_bytes(), "image/jpeg")},
            data={
                "capture_id": "clean-unpaired",
                "capture_time_ms": str(int(time.time() * 1000)),
                "camera_facing_mode": "environment",
                "mode": "sensor_assisted",
                "ground_truth_cm": "50",
            },
        )

    assert response.status_code == 409
    assert not (
        incoming_capture_root(tmp_path) / "records" / "clean-unpaired.json"
    ).exists()


def test_stored_capture_runs_as_one_independent_job_with_original_sensor_snapshot(monkeypatch, tmp_path) -> None:
    import app.routes.analyze as analyze_route

    gemma = RecordingGemmaClient()
    monkeypatch.setattr(analyze_route.settings, "results_dir", tmp_path)
    monkeypatch.setattr(analyze_route, "gemma_client", gemma)
    with TestClient(app) as client:
        app.state.sensor_bridge = RecordingSensorBridge()
        assert _create_capture(client).status_code == 201
        accepted = client.post("/captures/cap-001/analysis-jobs")
        duplicate = client.post("/captures/cap-001/analysis-jobs")
        result = None
        for _ in range(100):
            result = client.get(accepted.json()["poll_url"]).json()
            if result["status"] in {"completed", "failed"}:
                break
            time.sleep(0.01)
        stored = client.get(
            "/captures",
            params={"batch_id": CAPTURE_CANDIDATE_BATCH_ID},
        ).json()["captures"][0]

    assert accepted.status_code == 202
    assert duplicate.status_code == 409
    assert result is not None
    assert result["status"] == "completed"
    assert gemma.calls == 1
    assert result["result"]["sensor_evidence"]["capture_id"] == "cap-001"
    assert result["result"]["sensor_evidence"]["samples"]["sensor_1"]["distance_cm"] == 47.0
    assert stored["status"] == "completed"
    assert stored["analysis_run_id"] == result["result"]["analysis_run_id"]
    assert stored["analysis_attempts"] == 1


def test_orphaned_job_after_restart_can_be_retried(monkeypatch, tmp_path) -> None:
    import app.routes.analyze as analyze_route

    monkeypatch.setattr(analyze_route.settings, "results_dir", tmp_path)
    monkeypatch.setattr(analyze_route, "gemma_client", RecordingGemmaClient())
    with TestClient(app) as client:
        app.state.sensor_bridge = RecordingSensorBridge()
        assert _create_capture(client).status_code == 201
        repository = CaptureRepository(incoming_capture_root(tmp_path))
        repository.mark_queued("cap-001", job_id="job-from-old-process", mode="sensor_assisted")

        accepted = client.post("/captures/cap-001/analysis-jobs")
        result = None
        for _ in range(100):
            result = client.get(accepted.json()["poll_url"]).json()
            if result["status"] in {"completed", "failed"}:
                break
            time.sleep(0.01)

    assert accepted.status_code == 202
    assert result is not None
    assert result["status"] == "completed"
    stored = repository.get("cap-001")
    assert stored["analysis_attempts"] == 2
    assert stored["status"] == "completed"
