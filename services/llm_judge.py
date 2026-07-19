import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import httpx

from services.llm_judge_rubric import (
    JUDGE_RUBRIC_VERSION,
    JudgeMessage,
    JudgeAggregate,
    JudgeResult,
    aggregate_judgements,
    build_judge_messages,
    judge_schema,
    parse_judge_result,
)


class LLMJudgeError(RuntimeError):
    pass


class OpenAIImageJudge:
    def __init__(
        self,
        api_key: str,
        cache_dir: Path,
        model: str = "gpt-4o-mini-2024-07-18",
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("api_key must not be empty")
        self._api_key = api_key
        self._cache_dir = cache_dir
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    @property
    def model(self) -> str:
        return self._model

    async def judge(
        self,
        annotation: dict[str, str],
        prediction: dict[str, str],
        image_data_url: str,
        repeats: int = 3,
    ) -> JudgeAggregate:
        if repeats < 1:
            raise ValueError("repeats must be greater than 0")
        messages = build_judge_messages(annotation, prediction, image_data_url)
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with httpx.AsyncClient(headers=headers, timeout=self._timeout_seconds) as client:
            results = [
                await self._judge_once(client, messages, repeat_index)
                for repeat_index in range(repeats)
            ]
        return aggregate_judgements(results)

    async def _judge_once(
        self,
        client: httpx.AsyncClient,
        messages: list[JudgeMessage],
        repeat_index: int,
    ) -> JudgeResult:
        cache_path = self._cache_path(messages, repeat_index)
        if cache_path.exists():
            return parse_judge_result(json.loads(cache_path.read_text(encoding="utf-8")))
        payload = {
            "model": self._model,
            "temperature": 0,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "spatial_description_judgement",
                    "strict": True,
                    "schema": judge_schema(),
                },
            },
        }
        try:
            response = await client.post(f"{self._base_url}/chat/completions", json=payload)
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            result = parse_judge_result(parsed)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as exc:
            raise LLMJudgeError(f"LLM judge request failed: {exc}") from exc
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(asdict(result), ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        return result

    def _cache_path(self, messages: list[JudgeMessage], repeat_index: int) -> Path:
        cache_input = json.dumps(
            {
                "model": self._model,
                "rubric_version": JUDGE_RUBRIC_VERSION,
                "repeat_index": repeat_index,
                "messages": messages,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        digest = hashlib.sha256(cache_input.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.json"
