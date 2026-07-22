import pytest

from app.config import Settings
from models.gemma_client import DEFAULT_GEMMA_PROMPT, GemmaClient, GemmaClientError, GemmaResult


def test_default_prompt_uses_single_image_and_forbids_numeric_distance_claims() -> None:
    prompt = DEFAULT_GEMMA_PROMPT.lower()
    assert "satu gambar" in prompt
    assert "jangan mengklaim pengukuran jarak" in prompt
    assert "json valid" in prompt


@pytest.mark.anyio
async def test_mock_description_returns_structured_visual_evidence() -> None:
    result = await GemmaClient(Settings(gemma_mock=True)).describe_image("image-data")
    assert result.mock is True
    assert result.structured is not None
    assert result.structured["scene_type"] == "indoor"
    assert "bukti visual" in result.description


@pytest.mark.anyio
async def test_describe_image_sends_exactly_one_rgb_image(monkeypatch) -> None:
    client = GemmaClient(Settings(gemma_mock=False))
    captured = {}

    async def fake_complete(content, _started_at):
        captured["content"] = content
        return GemmaResult("Terlihat meja.", "{}", 1)

    monkeypatch.setattr(client, "_complete", fake_complete)
    await client.describe_image("rgb-data")
    image_parts = [part for part in captured["content"] if part["type"] == "image_url"]
    assert len(image_parts) == 1
    assert image_parts[0]["image_url"]["url"] == "data:image/jpeg;base64,rgb-data"


@pytest.mark.anyio
async def test_length_limited_response_raises_actionable_error(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, *_args, **_kwargs):
            return FakeResponse()

    monkeypatch.setattr("models.gemma_client.httpx.AsyncClient", lambda **_kwargs: FakeClient())
    with pytest.raises(GemmaClientError, match="batas 900 token"):
        await GemmaClient(Settings(gemma_mock=False)).describe_image("rgb-data")
