import io
import time

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from models.depth_anything import DepthResult
from models.gemma_client import GemmaResult


client = TestClient(app)


def _sample_image_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (40, 32), color=(150, 160, 120)).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_health_endpoint_returns_backend_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["backend"] == "ok"


def test_experiment_status_endpoint_returns_readiness_snapshot() -> None:
    response = client.get("/experiment-status")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "annotation_count" in data
    assert "dataset_image_count" in data
    assert "readiness_score" in data
    assert isinstance(data["readiness_notes"], list)
    assert data["artifact_profile"] == "final_44_gemma_e2b_20260708"
    assert data["dataset_image_count"] == 44
    assert data["annotation_count"] == 44
    assert data["artifact_paths"]["images"] == "dataset/final_images"


def test_analyze_endpoint_rejects_text_file() -> None:
    response = client.post(
        "/analyze",
        files={"image": ("notes.txt", b"hello", "text/plain")},
        data={"mode": "gemma_depth"},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False


def test_analyze_endpoint_returns_fused_result_with_mocks(monkeypatch) -> None:
    class FakeGemmaClient:
        async def describe_image(self, base64_image: str, prompt: str | None = None) -> GemmaResult:
            return GemmaResult("Terlihat kursi di tengah ruangan.", "{}", 5, mock=True)

    class FakeDepthModel:
        def estimate(self, image, source_name: str) -> DepthResult:
            depth_map = np.full((9, 9), 2.0, dtype=np.float32)
            depth_map[6:9, 3:6] = 0.7
            return DepthResult(True, depth_map, None, 4, depth_map.shape, mock=True)

    import app.routes.analyze as analyze_route

    monkeypatch.setattr(analyze_route, "gemma_client", FakeGemmaClient())
    monkeypatch.setattr(analyze_route, "depth_model", FakeDepthModel())

    response = client.post(
        "/analyze",
        files={"image": ("sample.jpg", _sample_image_bytes(), "image/jpeg")},
        data={"mode": "gemma_depth", "save_result": "false"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Berdasarkan grid depth 3x3" in data["final_description"]
    assert data["display"]["fusion_strategy"] == "evidence_constrained_regional_late_fusion"
    assert data["depth_summary"]["nearest_region"] == "lower_center"
    assert isinstance(data["latency"]["fusion_ms"], int)
    assert data["latency"]["fusion_ms"] >= 0


def test_analyze_endpoint_rejects_retired_prompted_mode() -> None:
    response = client.post(
        "/analyze",
        files={"image": ("sample.jpg", _sample_image_bytes(), "image/jpeg")},
        data={"mode": "gemma_depth_prompted", "save_result": "false"},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Mode must be one of gemma_only, depth_only, or gemma_depth."


def test_analysis_job_endpoint_returns_accepted_then_completed(monkeypatch) -> None:
    class FakeGemmaClient:
        async def describe_image(self, base64_image: str, prompt: str | None = None) -> GemmaResult:
            return GemmaResult("Terlihat kursi di tengah ruangan.", "{}", 5, mock=True)

    class FakeDepthModel:
        def estimate(self, image, source_name: str) -> DepthResult:
            depth_map = np.full((9, 9), 2.0, dtype=np.float32)
            depth_map[6:9, 3:6] = 0.7
            return DepthResult(True, depth_map, None, 4, depth_map.shape, mock=True)

    import app.routes.analyze as analyze_route

    monkeypatch.setattr(analyze_route, "gemma_client", FakeGemmaClient())
    monkeypatch.setattr(analyze_route, "depth_model", FakeDepthModel())

    with TestClient(app) as live_client:
        accepted = live_client.post(
            "/analysis-jobs",
            files={"image": ("sample.jpg", _sample_image_bytes(), "image/jpeg")},
            data={"mode": "gemma_depth", "save_result": "false"},
        )

        assert accepted.status_code == 202
        accepted_data = accepted.json()
        assert accepted_data["status"] == "queued"
        assert accepted_data["poll_url"].endswith(accepted_data["job_id"])

        result = None
        for _ in range(100):
            response = live_client.get(accepted_data["poll_url"])
            result = response.json()
            if result["status"] in {"completed", "failed"}:
                break
            time.sleep(0.01)

        assert result is not None
        assert result["status"] == "completed"
        assert result["result"]["success"] is True
