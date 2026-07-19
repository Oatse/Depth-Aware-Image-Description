from __future__ import annotations

import time
from dataclasses import dataclass

import anyio
import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from app.config import Settings


class ChatMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    content: str


class ChatChoice(BaseModel):
    model_config = ConfigDict(frozen=True)

    message: ChatMessage


class ChatEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)

    choices: tuple[ChatChoice, ...]


@dataclass(frozen=True, slots=True)
class StructuredRequest:
    image_base64: str
    prompt: str
    schema_name: str
    response_model: type[BaseModel]


@dataclass(frozen=True, slots=True)
class InferenceResult:
    content: str
    latency_ms: int


@dataclass(frozen=True, slots=True)
class GemmaResponseError(Exception):
    reason: str

    def __str__(self) -> str:
        return self.reason


async def check_model_ready(settings: Settings) -> bool:
    endpoint = settings.lm_studio_openai_base_url + "/models"
    try:
        async with httpx.AsyncClient(timeout=settings.lm_studio_health_timeout) as client:
            response = await client.get(endpoint)
            response.raise_for_status()
    except httpx.HTTPError:
        return False
    return True


async def infer_structured(settings: Settings, request: StructuredRequest) -> InferenceResult:
    started_at = time.perf_counter()
    payload = {
        "model": settings.lm_studio_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": request.prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{request.image_base64}"},
                    },
                ],
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": request.schema_name,
                "strict": True,
                "schema": request.response_model.model_json_schema(by_alias=True),
            },
        },
        "temperature": 0,
        "max_tokens": settings.lm_studio_max_tokens,
        "stream": False,
    }
    endpoint = settings.lm_studio_openai_base_url + "/chat/completions"
    try:
        with anyio.fail_after(settings.lm_studio_timeout):
            async with httpx.AsyncClient(timeout=settings.lm_studio_timeout) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                envelope = ChatEnvelope.model_validate(response.json())
    except TimeoutError as exc:
        raise GemmaResponseError("LM Studio timed out during structured inference.") from exc
    except httpx.HTTPError as exc:
        status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
        detail = f"HTTP {status}" if status is not None else "connection error"
        raise GemmaResponseError(f"LM Studio structured inference failed: {detail}.") from exc
    except (ValueError, ValidationError) as exc:
        raise GemmaResponseError("LM Studio returned an invalid chat-completion envelope.") from exc
    if not envelope.choices:
        raise GemmaResponseError("LM Studio returned no completion choice.")
    return InferenceResult(
        content=envelope.choices[0].message.content,
        latency_ms=int((time.perf_counter() - started_at) * 1000),
    )
