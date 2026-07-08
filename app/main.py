import csv
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict

from app.config import get_settings
from app.routes.analyze import router as analyze_router
from app.schemas import HealthResponse
from models.gemma_client import GemmaClient

settings = get_settings()
DATASET_DIR = Path("./dataset")


class EvaluationMetric(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: str
    total_images: int
    prediction_coverage: float
    object_accuracy: float
    position_accuracy: float
    distance_category_accuracy: float
    obstacle_warning_accuracy: float
    description_quality: float
    average_latency_ms: float


class ExperimentStatusResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    success: bool
    annotation_count: int
    dataset_image_count: int
    prediction_count: int
    predictions_by_mode: dict[str, int]
    evaluation: list[EvaluationMetric]
    readiness_score: int
    readiness_notes: list[str]

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Prototype implementasi depth-aware image description untuk citra indoor.",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/results", StaticFiles(directory=str(settings.results_dir)), name="results")
templates = Jinja2Templates(directory="templates")
app.include_router(analyze_router)
gemma_client = GemmaClient(settings)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        success=True,
        app=settings.app_name,
        backend="ok",
        gemma=await gemma_client.check_status(),
        depth_model=settings.depth_model_status,
    )


@app.get("/experiment-status", response_model=ExperimentStatusResponse)
async def experiment_status() -> ExperimentStatusResponse:
    annotations = _read_csv(DATASET_DIR / "annotations.csv")
    predictions = _read_csv(settings.results_dir / "predictions.csv")
    evaluation = [
        EvaluationMetric(
            mode=row.get("mode", "all") or "all",
            total_images=_to_int(row.get("total_images")),
            prediction_coverage=_to_float(row.get("prediction_coverage")),
            object_accuracy=_to_float(row.get("object_accuracy")),
            position_accuracy=_to_float(row.get("position_accuracy")),
            distance_category_accuracy=_to_float(row.get("distance_category_accuracy")),
            obstacle_warning_accuracy=_to_float(row.get("obstacle_warning_accuracy")),
            description_quality=_to_float(row.get("description_quality")),
            average_latency_ms=_to_float(row.get("average_latency_ms")),
        )
        for row in _read_csv(settings.results_dir / "evaluation.csv")
    ]
    dataset_image_count = _count_images(DATASET_DIR / "images")
    predictions_by_mode = _count_predictions_by_mode(predictions)
    readiness_score, readiness_notes = _readiness(annotations, dataset_image_count, predictions_by_mode, evaluation)

    return ExperimentStatusResponse(
        success=True,
        annotation_count=len(annotations),
        dataset_image_count=dataset_image_count,
        prediction_count=len(predictions),
        predictions_by_mode=predictions_by_mode,
        evaluation=evaluation,
        readiness_score=readiness_score,
        readiness_notes=readiness_notes,
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
    if not value:
        return 0
    try:
        return int(float(value))
    except ValueError:
        return 0


def _to_float(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0
