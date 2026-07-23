import json
import hashlib
import re
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any

import anyio
import httpx

from app.config import Settings


DEFAULT_GEMMA_PROMPT = (
    "Anda adalah sistem deskripsi gambar berbahasa Indonesia. "
    "Analisis satu gambar lingkungan indoor secara ringkas, jelas, dan praktis. "
    "Fokus pada objek utama, posisi objek, area depan, potensi hambatan yang benar-benar tampak, "
    "dan relasi spasial visual yang dapat dibaca langsung dari gambar. "
    "Boleh gunakan indikasi kualitatif seperti tampak dekat, tampak jauh, sisi kiri, sisi kanan, "
    "tengah, atau area depan jika terlihat jelas. Jangan mengklaim pengukuran jarak atau area aman. "
    "Jangan mengarang detail yang tidak terlihat. Gunakan bahasa hati-hati seperti 'terlihat', "
    "'tampak', atau 'kemungkinan' jika tidak yakin. Balas hanya JSON valid tanpa markdown dengan skema: "
    "{\"scene_type\":\"indoor|non_indoor|tidak_diketahui\","
    "\"main_object\":\"string\","
    "\"object_position\":\"kiri|kanan|tengah|depan|bawah|tidak_diketahui\","
    "\"objects\":[\"string\"],"
    "\"obstacle_candidate\":\"string\","
    "\"description\":\"maksimal dua kalimat Bahasa Indonesia\"}."
)


@dataclass(frozen=True, slots=True)
class GemmaResult:
    description: str
    raw_response: str
    latency_ms: int
    mock: bool = False
    structured: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None


class GemmaClientError(RuntimeError):
    pass


class GemmaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def check_status(self) -> str:
        if self.settings.gemma_mock:
            return "mock"
        endpoint = self.settings.lm_studio_url.rstrip("/") + "/api/v1/models"
        try:
            async with httpx.AsyncClient(timeout=self.settings.lm_studio_health_timeout) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return "error"

        for model in data.get("models", []):
            if not isinstance(model, dict) or model.get("key") != self.settings.lm_studio_model:
                continue
            loaded_instances = model.get("loaded_instances")
            return "ready" if isinstance(loaded_instances, list) and loaded_instances else "model_not_loaded"
        return "model_not_loaded"

    async def describe_image(self, base64_image: str, prompt: str | None = None) -> GemmaResult:
        started_at = time.perf_counter()
        prompt_text = prompt or DEFAULT_GEMMA_PROMPT
        request_started_at = datetime.now(timezone.utc).isoformat()
        if self.settings.gemma_mock:
            description = (
                "Terlihat area dalam ruangan dengan beberapa objek di sekitar ruangan. "
                "Posisi objek dijelaskan hanya berdasarkan bukti visual pada gambar."
            )
            return GemmaResult(
                description=description,
                raw_response='{\"mock\":true}',
                latency_ms=_elapsed_ms(started_at),
                mock=True,
                structured={
                    "scene_type": "indoor",
                    "main_object": "tidak_diketahui",
                    "object_position": "tengah",
                    "objects": [],
                    "obstacle_candidate": "tidak_diketahui",
                    "description": description,
                },
                provenance=_provenance(
                    settings=self.settings,
                    prompt=prompt_text,
                    raw_response='{"mock":true}',
                    request_started_at=request_started_at,
                    mock=True,
                ),
            )

        content = [
            {"type": "text", "text": prompt_text},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            },
        ]
        return await self._complete(content, started_at)

    async def _complete(
        self,
        content: list[dict[str, Any]],
        started_at: float,
        prompt: str | None = None,
        request_started_at: str | None = None,
    ) -> GemmaResult:
        prompt = prompt or str(content[0].get("text", DEFAULT_GEMMA_PROMPT))
        payload = {
            "model": self.settings.lm_studio_model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.1,
            "max_tokens": self.settings.lm_studio_max_tokens,
        }
        endpoint = self.settings.lm_studio_openai_base_url + "/chat/completions"
        try:
            with anyio.fail_after(self.settings.lm_studio_timeout):
                async with httpx.AsyncClient(timeout=self.settings.lm_studio_timeout) as client:
                    response = await client.post(endpoint, json=payload)
                    response.raise_for_status()
                    data = response.json()
        except TimeoutError as exc:
            raise GemmaClientError("Gemma inference timed out before returning a description.") from exc
        except httpx.HTTPError as exc:
            raise GemmaClientError(
                "Gemma inference failed. Please ensure LM Studio is running and the model is loaded."
            ) from exc
        except ValueError as exc:
            raise GemmaClientError("Gemma response was not valid JSON.") from exc

        try:
            choice = data["choices"][0]
            raw_text = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GemmaClientError("Gemma response did not contain a description.") from exc
        if choice.get("finish_reason") == "length":
            raise GemmaClientError(
                f"Gemma menghabiskan batas {self.settings.lm_studio_max_tokens} token sebelum menghasilkan deskripsi."
            )
        if not isinstance(raw_text, str) or not raw_text.strip():
            raise GemmaClientError("Gemma returned an empty description.")

        structured = _parse_structured_response(raw_text)
        description = _description_from_structured(structured) if structured else _sanitize_description(raw_text)
        if not description:
            raise GemmaClientError("Gemma returned an empty description.")
        return GemmaResult(
            description=description,
            raw_response=str(data),
            latency_ms=_elapsed_ms(started_at),
            structured=structured,
            provenance=_provenance(
                settings=self.settings,
                prompt=prompt,
                raw_response=str(data),
                request_started_at=request_started_at or datetime.now(timezone.utc).isoformat(),
                mock=False,
            ),
        )


def _sanitize_description(text: str) -> str:
    without_markdown = re.sub(r"(\*\*|__|`|#+)", "", text)
    without_bullets = re.sub(r"(?:^|\s)(?:[-*]|\d+[.)])\s+", " ", without_markdown)
    cleaned = " ".join(without_bullets.replace("\n", " ").split())
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    return " ".join(sentences[:2])[:420].strip()


def _parse_structured_response(text: str) -> dict[str, Any] | None:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate)
    json_match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
    if json_match:
        candidate = json_match.group(0)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None

    objects = parsed.get("objects")
    parsed["objects"] = [str(item) for item in objects[:8]] if isinstance(objects, list) else []
    for key in ("scene_type", "main_object", "object_position", "obstacle_candidate", "description"):
        value = parsed.get(key)
        parsed[key] = str(value).strip() if value else "tidak_diketahui"
    allowed_positions = {"kiri", "kanan", "tengah", "depan", "bawah", "tidak_diketahui"}
    if parsed["object_position"] not in allowed_positions:
        parsed["object_position"] = "tidak_diketahui"
    return parsed


def _description_from_structured(structured: dict[str, Any] | None) -> str:
    if not structured:
        return ""
    description = _sanitize_description(str(structured.get("description", "")))
    if description and description != "tidak_diketahui":
        return description
    main_object = structured.get("main_object", "tidak_diketahui")
    position = structured.get("object_position", "tidak_diketahui")
    if main_object != "tidak_diketahui":
        return f"Terlihat {main_object} di area {position}."
    return "Deskripsi visual tidak tersedia secara memadai."


def _elapsed_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)


def _provenance(
    *,
    settings: Settings,
    prompt: str,
    raw_response: str,
    request_started_at: str,
    mock: bool,
) -> dict[str, Any]:
    return {
        "app_version": "0.1.0",
        "provider": "mock" if mock else "lm_studio",
        "model_id": settings.lm_studio_model,
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "temperature": 0.1,
        "max_tokens": settings.lm_studio_max_tokens,
        "request_started_at": request_started_at,
        "raw_response": raw_response,
        "mock": mock,
    }
