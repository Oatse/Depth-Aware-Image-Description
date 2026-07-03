import io

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
        async def describe_image(self, base64_image: str) -> GemmaResult:
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
    assert "Berdasarkan estimasi kedalaman" in data["final_description"]
    assert data["depth_summary"]["nearest_region"] == "lower_center"
    assert isinstance(data["latency"]["fusion_ms"], int)
    assert data["latency"]["fusion_ms"] >= 0
