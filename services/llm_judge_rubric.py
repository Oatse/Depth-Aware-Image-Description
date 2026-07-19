import json
import statistics
from dataclasses import dataclass
from typing import Literal, TypedDict


JUDGE_RUBRIC_VERSION = "spatial-description-judge-v2-image-aware"
ANNOTATION_FIELDS = (
    "main_object",
    "object_position",
    "distance_category",
    "has_obstacle",
    "front_area_status",
    "open_area",
    "safer_direction",
    "annotation_confidence",
)


class ImageUrl(TypedDict):
    url: str
    detail: Literal["high"]


class TextContent(TypedDict):
    type: Literal["text"]
    text: str


class ImageContent(TypedDict):
    type: Literal["image_url"]
    image_url: ImageUrl


class SystemMessage(TypedDict):
    role: Literal["system"]
    content: str


class UserMessage(TypedDict):
    role: Literal["user"]
    content: list[TextContent | ImageContent]


JudgeMessage = SystemMessage | UserMessage


@dataclass(frozen=True, slots=True)
class JudgeResult:
    semantic_correctness: int
    spatial_accuracy: int
    groundedness: int
    clarity: int
    overall: int
    rationale: str
    visual_evidence: tuple[str, ...]
    critical_errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class JudgeAggregate:
    repeat_count: int
    semantic_correctness_mean: float
    spatial_accuracy_mean: float
    groundedness_mean: float
    clarity_mean: float
    overall_mean: float
    overall_stddev: float
    visual_evidence_union: tuple[str, ...]
    critical_error_union: tuple[str, ...]


def build_judge_messages(
    annotation: dict[str, str],
    prediction: dict[str, str],
    image_data_url: str,
) -> list[JudgeMessage]:
    reference = {
        field: annotation.get(field, "")
        for field in ANNOTATION_FIELDS
        if annotation.get(field, "").strip()
    }
    system_message = (
        "Anda adalah evaluator deskripsi visual-spasial indoor berbahasa Indonesia. "
        "Gunakan citra sebagai bukti visual utama dan anotasi terstruktur sebagai label pembanding sekunder. "
        "Nilai hanya fakta yang dapat diperiksa dari citra atau label pembanding. "
        "Jangan menghukum detail kandidat yang terlihat pada citra hanya karena detail tersebut tidak ada dalam anotasi. "
        "Nama metode eksperimen sengaja disembunyikan. Gunakan skor integer 1-5 dan rubric yang sama untuk setiap kandidat. "
        "Keluarkan hanya satu objek JSON valid tanpa markdown atau teks tambahan, dengan field "
        "semantic_correctness, spatial_accuracy, groundedness, clarity, overall, rationale, visual_evidence, dan critical_errors. "
        "Field visual_evidence dan critical_errors harus berupa array string."
    )
    user_message = json.dumps(
        {
            "rubric_version": JUDGE_RUBRIC_VERSION,
            "rubric": {
                "semantic_correctness": "Kesesuaian objek dan isi semantik dengan bukti pada citra.",
                "spatial_accuracy": "Kesesuaian posisi, jarak relatif, status halangan, dan arah dengan citra serta label pembanding.",
                "groundedness": "Tidak menambahkan klaim yang bertentangan dengan citra.",
                "clarity": "Kejelasan dan keterbacaan bahasa Indonesia.",
                "overall": "Bobot terbesar pada kebenaran spasial dan groundedness.",
            },
            "structured_annotation": reference,
            "candidate_description": prediction.get("final_description", "").strip(),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return [
        {"role": "system", "content": system_message},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_message},
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_url, "detail": "high"},
                },
            ],
        },
    ]


def aggregate_judgements(judgements: list[JudgeResult]) -> JudgeAggregate:
    if not judgements:
        raise ValueError("At least one judgement is required.")
    overall_scores = [result.overall for result in judgements]
    visual_evidence = sorted({evidence for result in judgements for evidence in result.visual_evidence})
    critical_errors = sorted({error for result in judgements for error in result.critical_errors})
    return JudgeAggregate(
        repeat_count=len(judgements),
        semantic_correctness_mean=statistics.fmean(result.semantic_correctness for result in judgements),
        spatial_accuracy_mean=statistics.fmean(result.spatial_accuracy for result in judgements),
        groundedness_mean=statistics.fmean(result.groundedness for result in judgements),
        clarity_mean=statistics.fmean(result.clarity for result in judgements),
        overall_mean=statistics.fmean(overall_scores),
        overall_stddev=statistics.pstdev(overall_scores),
        visual_evidence_union=tuple(visual_evidence),
        critical_error_union=tuple(critical_errors),
    )


def parse_judge_result(payload: dict[str, object]) -> JudgeResult:
    score_fields = ("semantic_correctness", "spatial_accuracy", "groundedness", "clarity", "overall")
    scores = {field: int(payload[field]) for field in score_fields}
    if any(score < 1 or score > 5 for score in scores.values()):
        raise ValueError("Judge scores must be between 1 and 5.")
    raw_errors = payload.get("critical_errors", [])
    if not isinstance(raw_errors, list) or not all(isinstance(error, str) for error in raw_errors):
        raise ValueError("critical_errors must be a list of strings.")
    rationale = payload.get("rationale", "")
    if not isinstance(rationale, str):
        raise ValueError("rationale must be a string.")
    raw_evidence = payload.get("visual_evidence", [])
    if not isinstance(raw_evidence, list) or not all(isinstance(evidence, str) for evidence in raw_evidence):
        raise ValueError("visual_evidence must be a list of strings.")
    return JudgeResult(
        semantic_correctness=scores["semantic_correctness"],
        spatial_accuracy=scores["spatial_accuracy"],
        groundedness=scores["groundedness"],
        clarity=scores["clarity"],
        overall=scores["overall"],
        rationale=rationale,
        visual_evidence=tuple(raw_evidence),
        critical_errors=tuple(raw_errors),
    )


def judge_schema() -> dict[str, object]:
    score = {"type": "integer", "minimum": 1, "maximum": 5}
    properties = {field: score for field in (
        "semantic_correctness",
        "spatial_accuracy",
        "groundedness",
        "clarity",
        "overall",
    )}
    properties.update({
        "rationale": {"type": "string"},
        "visual_evidence": {"type": "array", "items": {"type": "string"}},
        "critical_errors": {"type": "array", "items": {"type": "string"}},
    })
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }
