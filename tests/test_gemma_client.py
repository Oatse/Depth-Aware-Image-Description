from typing import TypedDict

import anyio
import pytest

from app.config import Settings
from models.gemma_client import (
    DEFAULT_GEMMA_PROMPT,
    GemmaClient,
    GemmaClientError,
    _parse_structured_response,
)


class FakeGemmaMessage(TypedDict):
    content: str


class FakeGemmaChoice(TypedDict):
    message: FakeGemmaMessage


class FakeGemmaResponsePayload(TypedDict):
    choices: list[FakeGemmaChoice]


def test_default_gemma_prompt_frames_baseline_as_visual_spatial_not_depth_measurement() -> None:
    assert "baseline Gemma tanpa metadata depth" in DEFAULT_GEMMA_PROMPT
    assert "relasi spasial visual" in DEFAULT_GEMMA_PROMPT
    assert "Jangan mengklaim pengukuran jarak" in DEFAULT_GEMMA_PROMPT


def test_default_token_budget_is_bounded_for_two_sentence_descriptions() -> None:
    settings = Settings()

    assert settings.lm_studio_max_tokens <= 1000


def test_mock_description_does_not_restore_retired_depth_prompting_behavior() -> None:
    # Given
    client = GemmaClient(Settings(gemma_mock=True))

    # When
    result = anyio.run(
        client.describe_image,
        "base64-image",
        "Depth-to-Spatial Prompting Schema from a retired experiment",
    )

    # Then
    assert "depth-to-spatial prompting" not in result.description.lower()
    assert "tanpa metadata depth eksplisit" in result.description


def test_describe_image_uses_configured_token_budget(monkeypatch) -> None:
    captured_payload = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> FakeGemmaResponsePayload:
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
    assert captured_payload["temperature"] == 0.1
    assert result.description == "Terlihat kursi di tengah ruangan."


def test_describe_image_fails_when_runtime_exceeds_configured_timeout(monkeypatch) -> None:
    class SlowAsyncClient:
        def __init__(self, timeout: int) -> None:
            self.timeout = timeout

        async def __aenter__(self) -> "SlowAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def post(self, endpoint: str, json: dict) -> None:
            await anyio.sleep(1)

    monkeypatch.setattr("models.gemma_client.httpx.AsyncClient", SlowAsyncClient)

    settings = Settings(lm_studio_timeout=0)

    with pytest.raises(GemmaClientError, match="timed out"):
        anyio.run(GemmaClient(settings).describe_image, "base64-image")


def test_structured_parser_rejects_compound_position_outside_declared_schema() -> None:
    # Given
    raw = (
        '{"scene_type":"indoor","main_object":"kursi",'
        '"object_position":"tengah|kanan","objects":[],"obstacle_candidate":"kursi",'
        '"description":"Terlihat kursi."}'
    )

    # When
    parsed = _parse_structured_response(raw)

    # Then
    assert parsed is not None
    assert parsed["object_position"] == "tidak_diketahui"
