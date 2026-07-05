import json
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings


DEFAULT_GEMMA_PROMPT = (
    "Anda adalah sistem image description berbahasa Indonesia. "
    "Analisis gambar lingkungan indoor secara ringkas, jelas, dan praktis sebagai baseline Gemma tanpa metadata depth. "
    "Fokus pada objek utama, posisi objek, area depan, potensi hambatan yang tampak, dan relasi spasial visual yang dapat dibaca langsung dari gambar. "
    "Boleh gunakan indikasi kualitatif seperti tampak dekat, tampak jauh, sisi kiri, sisi kanan, tengah, atau area depan jika terlihat jelas. "
    "Jangan mengklaim pengukuran jarak, peta kedalaman, region depth, atau area aman karena mode ini tidak menerima metadata depth eksplisit. "
    "Jangan mengarang detail yang tidak terlihat. "
    "Gunakan bahasa hati-hati seperti 'terlihat', 'tampak', atau 'kemungkinan' jika tidak yakin. "
    "Balas hanya JSON valid tanpa markdown dengan skema: "
    "{\"scene_type\":\"indoor|non_indoor|tidak_diketahui\","
    "\"main_object\":\"string\","
    "\"object_position\":\"kiri|kanan|tengah|depan|bawah|tidak_diketahui\","
    "\"objects\":[\"string\"],"
    "\"obstacle_candidate\":\"string\","
    "\"description\":\"maksimal dua kalimat Bahasa Indonesia\"}."
)


@dataclass(frozen=True)
class GemmaResult:
    description: str
    raw_response: str
    latency_ms: int
    mock: bool = False
    structured: dict[str, Any] | None = None


class GemmaClientError(RuntimeError):
    pass


class GemmaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def check_status(self) -> str:
        if self.settings.gemma_mock:
            return "mock"

        endpoint = self.settings.lm_studio_openai_base_url + "/models"
        try:
            async with httpx.AsyncClient(timeout=self.settings.lm_studio_health_timeout) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return "error"

        model_ids = _extract_model_ids(data)
        if not model_ids:
            return "ready"
        return "ready" if self.settings.lm_studio_model in model_ids else "model_not_loaded"

    async def describe_image(self, base64_image: str, prompt: str | None = None) -> GemmaResult:
        started_at = time.perf_counter()
        prompt_text = prompt or DEFAULT_GEMMA_PROMPT
        if self.settings.gemma_mock:
            is_prompted = "Depth-to-Spatial Prompting Schema" in prompt_text
            description = (
                "Terlihat area dalam ruangan dengan beberapa objek dan konteks kedalaman relatif. "
                "Deskripsi ini berasal dari mock eksplisit untuk mode depth-to-spatial prompting."
                if is_prompted
                else (
                    "Terlihat area dalam ruangan dengan beberapa objek di sekitar ruangan. "
                    "Objek dan area depan dijelaskan sebagai indikasi visual tanpa metadata depth eksplisit."
                )
            )
            return GemmaResult(
                description=description,
                raw_response='{"mock": true}',
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
            )

        payload = {
            "model": self.settings.lm_studio_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            "temperature": 0.2,
            "max_tokens": self.settings.lm_studio_max_tokens,
        }

        endpoint = self.settings.lm_studio_openai_base_url + "/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=self.settings.lm_studio_timeout) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise GemmaClientError(
                "Gemma inference failed. Please ensure LM Studio is running and the model is loaded."
            ) from exc
        except ValueError as exc:
            raise GemmaClientError("Gemma response was not valid JSON.") from exc

        try:
            raw_text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GemmaClientError("Gemma response did not contain a description.") from exc

        structured = _parse_structured_response(str(raw_text))
        description = _description_from_structured(structured) if structured else _sanitize_description(str(raw_text))
        if not description:
            raise GemmaClientError("Gemma returned an empty description.")

        return GemmaResult(
            description=description,
            raw_response=str(data),
            latency_ms=_elapsed_ms(started_at),
            structured=structured,
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
    if not isinstance(objects, list):
        parsed["objects"] = []
    else:
        parsed["objects"] = [str(item) for item in objects[:8]]

    for key in ["scene_type", "main_object", "object_position", "obstacle_candidate", "description"]:
        value = parsed.get(key)
        parsed[key] = str(value).strip() if value else "tidak_diketahui"
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


def _extract_model_ids(data: dict) -> set[str]:
    raw_models = data.get("data", [])
    model_ids: set[str] = set()
    for model in raw_models:
        if isinstance(model, dict) and isinstance(model.get("id"), str):
            model_ids.add(model["id"])
    return model_ids


def _elapsed_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)
