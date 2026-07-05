import anyio

from app.config import Settings
from models.gemma_client import DEFAULT_GEMMA_PROMPT, GemmaClient


def test_default_gemma_prompt_frames_baseline_as_visual_spatial_not_depth_measurement() -> None:
    assert "baseline Gemma tanpa metadata depth" in DEFAULT_GEMMA_PROMPT
    assert "relasi spasial visual" in DEFAULT_GEMMA_PROMPT
    assert "Jangan mengklaim pengukuran jarak" in DEFAULT_GEMMA_PROMPT


def test_describe_image_uses_configured_token_budget(monkeypatch) -> None:
    captured_payload = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"description":"Terlihat kursi di tengah ruangan."}',
                        },
                    },
                ],
            }

    class FakeAsyncClient:
        def __init__(self, timeout: int) -> None:
            self.timeout = timeout

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def post(self, endpoint: str, json: dict) -> FakeResponse:
            captured_payload.update(json)
            return FakeResponse()

    monkeypatch.setattr("models.gemma_client.httpx.AsyncClient", FakeAsyncClient)

    settings = Settings(lm_studio_max_tokens=1200)
    result = anyio.run(GemmaClient(settings).describe_image, "base64-image")

    assert captured_payload["max_tokens"] == 1200
    assert result.description == "Terlihat kursi di tengah ruangan."
