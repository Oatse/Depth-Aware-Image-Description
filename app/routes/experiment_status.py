import csv
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.config import get_settings


router = APIRouter()
settings = get_settings()
class EvaluationMetric(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: str
    total_images: int
    prediction_coverage: float
    object_accuracy: float
    position_accuracy: float
    distance_category_accuracy: float | None
    obstacle_warning_accuracy: float | None
    obstacle_precision: float | None = None
    obstacle_recall: float | None = None
    obstacle_f1: float | None = None
    obstacle_true_positive: int | None = None
    obstacle_false_positive: int | None = None
    obstacle_true_negative: int | None = None
    obstacle_false_negative: int | None = None
    description_quality: float
    average_latency_ms: float


class ExperimentStatusResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    success: bool
    artifact_profile: str
    artifact_paths: dict[str, str]
    annotation_count: int
    dataset_image_count: int
    prediction_count: int
    predictions_by_mode: dict[str, int]
    evaluation: list[EvaluationMetric]
    readiness_score: int
    readiness_notes: list[str]


@router.get("/experiment-status", response_model=ExperimentStatusResponse)
async def experiment_status() -> ExperimentStatusResponse:
    annotations = _read_csv(settings.experiment_annotations_path)
    predictions = _read_csv(settings.experiment_predictions_path)
    evaluation = [_evaluation_metric(row) for row in _read_csv(settings.experiment_evaluation_path)]
    dataset_image_count = _count_images(settings.experiment_images_dir)
    predictions_by_mode = _count_predictions_by_mode(predictions)
    readiness_score, readiness_notes = _readiness(
        annotations,
        dataset_image_count,
        predictions_by_mode,
        evaluation,
    )
    return ExperimentStatusResponse(
        success=True,
        artifact_profile=settings.experiment_artifact_profile,
        artifact_paths={
            "images": settings.experiment_images_dir.as_posix().removeprefix("./"),
            "annotations": settings.experiment_annotations_path.as_posix().removeprefix("./"),
            "predictions": settings.experiment_predictions_path.as_posix().removeprefix("./"),
            "evaluation": settings.experiment_evaluation_path.as_posix().removeprefix("./"),
        },
        annotation_count=len(annotations),
        dataset_image_count=dataset_image_count,
        prediction_count=len(predictions),
        predictions_by_mode=predictions_by_mode,
        evaluation=evaluation,
        readiness_score=readiness_score,
        readiness_notes=readiness_notes,
    )


def _evaluation_metric(row: dict[str, str]) -> EvaluationMetric:
    return EvaluationMetric(
        mode=row.get("mode", "all") or "all",
        total_images=_to_int(row.get("total_images")),
        prediction_coverage=_to_float(row.get("prediction_coverage")),
        object_accuracy=_to_float(row.get("object_accuracy")),
        position_accuracy=_to_float(row.get("position_accuracy")),
        distance_category_accuracy=_to_optional_float(row.get("distance_category_accuracy")),
        obstacle_warning_accuracy=_to_optional_float(row.get("obstacle_warning_accuracy")),
        obstacle_precision=_to_optional_float(row.get("obstacle_precision")),
        obstacle_recall=_to_optional_float(row.get("obstacle_recall")),
        obstacle_f1=_to_optional_float(row.get("obstacle_f1")),
        obstacle_true_positive=_to_optional_int(row.get("obstacle_true_positive")),
        obstacle_false_positive=_to_optional_int(row.get("obstacle_false_positive")),
        obstacle_true_negative=_to_optional_int(row.get("obstacle_true_negative")),
        obstacle_false_negative=_to_optional_int(row.get("obstacle_false_negative")),
        description_quality=_to_float(row.get("description_quality")),
        average_latency_ms=_to_float(row.get("average_latency_ms")),
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _count_images(path: Path) -> int:
    if not path.exists():
        return 0
    suffixes = {".jpg", ".jpeg", ".png", ".webp"}
    return sum(1 for item in path.iterdir() if item.is_file() and item.suffix.lower() in suffixes)


def _count_predictions_by_mode(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        mode = row.get("mode", "unknown") or "unknown"
        counts[mode] = counts.get(mode, 0) + 1
    return counts


def _readiness(
    annotations: list[dict[str, str]],
    dataset_image_count: int,
    predictions_by_mode: dict[str, int],
    evaluation: list[EvaluationMetric],
) -> tuple[int, list[str]]:
    score = 20
    notes: list[str] = []
    if dataset_image_count >= 30:
        score += 25
        notes.append("Dataset gambar sudah mencapai batas minimal eksperimen skripsi.")
    else:
        notes.append("Dataset gambar masih perlu dilengkapi minimal 30 gambar indoor aktual.")
    if len(annotations) >= 30:
        score += 25
        notes.append("Anotasi manual sudah cukup untuk evaluasi kuantitatif.")
    else:
        notes.append("Anotasi manual belum cukup untuk menyimpulkan peningkatan mode fusion.")
    if predictions_by_mode.get("gemma_only", 0) > 0 and predictions_by_mode.get("gemma_depth", 0) > 0:
        score += 20
        notes.append("Prediksi sudah memuat mode pembanding Gemma only dan Gemma + Depth.")
    else:
        notes.append("Prediksi perlu memuat perbandingan gemma_only dan gemma_depth pada gambar yang sama.")
    if evaluation:
        score += 10
        notes.append("File evaluasi tersedia, tetapi tetap perlu dicek sinkron dengan dataset final.")
    else:
        notes.append("Ringkasan evaluasi belum tersedia.")
    return min(score, 100), notes


def _to_int(value: str | None) -> int:
    try:
        return int(float(value)) if value else 0
    except ValueError:
        return 0


def _to_float(value: str | None) -> float:
    try:
        return float(value) if value else 0.0
    except ValueError:
        return 0.0


def _to_optional_float(value: str | None) -> float | None:
    try:
        return float(value) if value else None
    except ValueError:
        return None


def _to_optional_int(value: str | None) -> int | None:
    try:
        return int(float(value)) if value else None
    except ValueError:
        return None
