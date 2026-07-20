import anyio
import numpy as np

from app.config import Settings
from models.depth_anything import DepthResult
from models.gemma_client import GemmaClientError, GemmaResult
from services.evidence_pipeline import build_evidence_bundle


def _image_bytes() -> bytes:
    from PIL import Image
    from io import BytesIO

    output = BytesIO()
    Image.new("RGB", (8, 8), "white").save(output, format="JPEG")
    return output.getvalue()


class FakeGemma:
    def __init__(self, fail=False):
        self.calls = 0
        self.fail = fail

    async def describe_image(self, _base64):
        self.calls += 1
        if self.fail:
            raise GemmaClientError("offline")
        return GemmaResult("terlihat meja", {"description": "terlihat meja"}, 3, mock=True)


class FakeDepth:
    def __init__(self, fail=False):
        self.calls = 0
        self.fail = fail

    def estimate(self, _image, _filename):
        self.calls += 1
        if self.fail:
            return DepthResult(False, None, "depth offline", 4, None, mock=False)
        return DepthResult(True, np.ones((9, 9), dtype=np.float32), None, 4, (9, 9), mock=True)


def test_bundle_runs_each_model_once_and_is_reusable() -> None:
    gemma = FakeGemma()
    depth = FakeDepth()
    async def run():
        return await build_evidence_bundle(
            _image_bytes(), "sample.jpg", Settings(gemma_mock=True, depth_mock=True),
            include_gemma=True, include_depth=True, gemma_client=gemma, depth_model=depth,
        )
    bundle = anyio.run(run)
    assert gemma.calls == 1
    assert depth.calls == 1
    assert bundle.gemma_description == "terlihat meja"
    assert bundle.depth_summary is not None


def test_bundle_keeps_failure_isolation_explicit() -> None:
    async def run():
        return await build_evidence_bundle(
            _image_bytes(), "sample.jpg", Settings(gemma_mock=True, depth_mock=True),
            include_gemma=True, include_depth=True, gemma_client=FakeGemma(fail=True), depth_model=FakeDepth(),
        )
    bundle = anyio.run(run)
    assert bundle.gemma_error == "offline"
    assert bundle.depth_summary is not None
