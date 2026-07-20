import time
from io import BytesIO

import anyio
import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

import app.routes.analyze as analyze_route
from app.config import Settings
from app.main import app
from models.depth_anything import DepthResult
from models.gemma_client import GemmaResult
from services.comparison_pipeline import ComparisonJobRequest, compare_image_bytes


def _image_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (8, 8), "white").save(output, format="JPEG")
    return output.getvalue()


class CountingGemma:
    def __init__(self):
        self.calls = 0

    async def describe_image(self, _base64):
        self.calls += 1
        return GemmaResult("Terlihat meja.", {"description": "Terlihat meja."}, 3, mock=True)


class CountingDepth:
    def __init__(self):
        self.calls = 0

    def estimate(self, _image, _filename):
        self.calls += 1
        depth = np.ones((9, 9), dtype=np.float32)
        return DepthResult(True, depth, None, 4, depth.shape, mock=True)


def _request() -> ComparisonJobRequest:
    return ComparisonJobRequest(
        _image_bytes(), "same.jpg", "image/jpeg", 8, 8, "cap-1",
        {
            "status": "paired",
            "samples": {
                "sensor_1": {"distance_cm": 80},
                "sensor_2": {"distance_cm": 82},
            },
        },
    )


def test_comparison_reuses_one_gemma_and_depth_inference() -> None:
    gemma = CountingGemma()
    depth = CountingDepth()

    async def run():
        return await compare_image_bytes(_request(), Settings(gemma_mock=True, depth_mock=True), gemma, depth)

    result = anyio.run(run)
    assert gemma.calls == 1
    assert depth.calls == 1
    assert set(result["modes"]) == {"gemma_only", "gemma_depth", "iot_assisted"}
    assert result["capture_id"] == "cap-1"
    assert result["modes"]["iot_assisted"]["sensor_contribution"]["status"] == "applied"


def test_comparison_job_endpoint_returns_backend_owned_modes(monkeypatch) -> None:
    gemma = CountingGemma()
    depth = CountingDepth()
    monkeypatch.setattr(analyze_route, "gemma_client", gemma)
    monkeypatch.setattr(analyze_route, "depth_model", depth)
    with TestClient(app) as client:
        accepted = client.post(
            "/analysis-comparisons",
            files={"image": ("same.jpg", _image_bytes(), "image/jpeg")},
            data={"capture_id": "cap-api"},
        )
        assert accepted.status_code == 202
        result = None
        for _ in range(100):
            state = client.get(accepted.json()["poll_url"]).json()
            if state["status"] in {"completed", "failed"}:
                result = state["result"]
                break
            time.sleep(0.01)
    assert result is not None
    assert set(result["modes"]) == {"gemma_only", "gemma_depth", "iot_assisted"}
    assert gemma.calls == 1
    assert depth.calls == 1
