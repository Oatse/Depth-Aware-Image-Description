import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

import anyio

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import Settings, get_settings
from models.depth_anything import DepthAnything
from models.gemma_client import GemmaClient
from services.evaluator import evaluate_predictions
from services.experiment_preflight import (
    EXPERIMENT_MODES,
    GEMMA_MODES,
    IMAGE_EXTENSIONS,
    ExperimentPreflightConfig,
    ExperimentPreflightError,
    ExperimentPreflightReport,
    run_experiment_preflight,
)
from services.pipeline import analyze_image_bytes, prediction_row
from services.result_logger import PREDICTION_FIELDS


DEFAULT_MODES = ("gemma_only", "depth_only", "gemma_depth")


@dataclass(frozen=True, slots=True)
class BatchRunConfig:
    images_dir: Path
    annotations_path: Path
    predictions_path: Path
    evaluation_path: Path
    modes: tuple[str, ...]
    allow_mock: bool = False
    preflight_only: bool = False
    resume: bool = False
    limit_jobs: int | None = None


@dataclass(frozen=True, slots=True)
class ExperimentJob:
    image_path: Path
    mode: str

    @property
    def key(self) -> tuple[str, str]:
        return (self.image_path.name, self.mode)


@dataclass(frozen=True, slots=True)
class RuntimeClients:
    settings: Settings
    gemma_client: GemmaClient
    depth_model: DepthAnything


async def run_batch(config: BatchRunConfig) -> None:
    settings = get_settings()
    preflight_report = run_experiment_preflight(
        ExperimentPreflightConfig(
            images_dir=config.images_dir,
            annotations_path=config.annotations_path,
            modes=config.modes,
            allow_mock=config.allow_mock,
        ),
        settings,
    )
    gemma_client = GemmaClient(settings)
    await _ensure_gemma_ready(config, gemma_client)
    _print_preflight_report(preflight_report)
    if config.preflight_only:
        return

    depth_model = DepthAnything(settings)
    image_paths = sorted(path for path in config.images_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)
    jobs = [
        ExperimentJob(image_path=image_path, mode=mode)
        for image_path in image_paths
        for mode in config.modes
    ]
    completed_jobs = _read_successful_job_keys(config.predictions_path) if config.resume else set()
    pending_jobs = [job for job in jobs if job.key not in completed_jobs]
    selected_jobs = pending_jobs[: config.limit_jobs] if config.limit_jobs is not None else pending_jobs

    _print_job_report(len(jobs), len(completed_jobs), len(selected_jobs))
    await _write_predictions(
        config,
        selected_jobs,
        RuntimeClients(settings=settings, gemma_client=gemma_client, depth_model=depth_model),
    )

    remaining_after_run = len(pending_jobs) - len(selected_jobs)
    if remaining_after_run > 0:
        print(f"Partial run complete. Remaining jobs: {remaining_after_run}. Run the same command again with --resume.")
        return

    summary = evaluate_predictions(config.annotations_path, config.predictions_path, config.evaluation_path)
    print("Evaluation Summary:")
    print(f"- Total images: {summary.total_images}")
    print(f"- Object accuracy: {_format_optional_percent(summary.object_accuracy)}")
    print(f"- Position accuracy: {_format_optional_percent(summary.position_accuracy)}")
    print(
        "- Object-position joint accuracy: "
        f"{_format_optional_percent(summary.object_position_joint_accuracy)}"
    )
    print(f"- Distance category accuracy: {_format_optional_percent(summary.distance_category_accuracy)}")
    print(f"- Obstacle warning accuracy: {_format_optional_percent(summary.obstacle_warning_accuracy)}")
    print(f"- Obstacle precision: {_format_optional_percent(summary.obstacle_precision)}")
    print(f"- Obstacle recall: {_format_optional_percent(summary.obstacle_recall)}")
    print(f"- Obstacle F1: {_format_optional_percent(summary.obstacle_f1)}")
    print(f"- Average latency: {summary.average_latency_ms:.1f} ms")


async def _ensure_gemma_ready(config: BatchRunConfig, gemma_client: GemmaClient) -> None:
    if not any(mode in GEMMA_MODES for mode in config.modes):
        return
    status = await gemma_client.check_status()
    if status in {"ready", "mock"}:
        return
    raise ExperimentPreflightError((
        f"Gemma runtime belum ready: {status}. Pastikan LM Studio berjalan dan model sudah loaded.",
    ))


def _print_preflight_report(report: ExperimentPreflightReport) -> None:
    print("Experiment preflight passed:")
    print(f"- Images: {report.image_count}")
    print(f"- Annotations: {report.annotation_count}")
    print(f"- Modes: {', '.join(report.modes)}")
    print(f"- Depth model: {report.depth_model_status}")
    for warning in report.warnings:
        print(f"- Warning: {warning}")


def _read_successful_job_keys(predictions_path: Path) -> set[tuple[str, str]]:
    if not predictions_path.exists():
        return set()
    with predictions_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {
        (row.get("image_name", ""), row.get("mode", ""))
        for row in rows
        if row.get("image_name") and row.get("mode") and not row.get("error")
    }


def _print_job_report(total_jobs: int, completed_jobs: int, selected_jobs: int) -> None:
    print(f"- Jobs total: {total_jobs}")
    print(f"- Jobs already successful: {completed_jobs}")
    print(f"- Jobs selected this run: {selected_jobs}")


def _format_optional_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2%}"


async def _write_predictions(
    config: BatchRunConfig,
    jobs: list[ExperimentJob],
    runtime: RuntimeClients,
) -> None:
    config.predictions_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not config.predictions_path.exists() or config.predictions_path.stat().st_size == 0
    mode = "a" if config.resume and config.predictions_path.exists() else "w"
    with config.predictions_path.open(mode, newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREDICTION_FIELDS)
        if write_header:
            writer.writeheader()
        for job in jobs:
            image_bytes = job.image_path.read_bytes()
            result = await analyze_image_bytes(
                image_bytes=image_bytes,
                filename=job.image_path.name,
                mode=job.mode,
                settings=runtime.settings,
                gemma_client=runtime.gemma_client,
                depth_model=runtime.depth_model,
            )
            writer.writerow(prediction_row(result))
            handle.flush()
            print(f"{job.image_path.name} | {job.mode} | success={result.success} | error={result.error or '-'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Gemma-only and Gemma+Depth batch evaluation.")
    parser.add_argument("--images-dir", type=Path, default=Path("dataset/images"))
    parser.add_argument("--annotations", type=Path, default=Path("dataset/annotations.csv"))
    parser.add_argument("--predictions", type=Path, default=Path("results/predictions.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/evaluation.csv"))
    parser.add_argument("--modes", nargs="+", choices=sorted(EXPERIMENT_MODES), default=list(DEFAULT_MODES))
    parser.add_argument("--allow-mock", action="store_true", help="Allow mock runtime for dry runs only.")
    parser.add_argument("--preflight-only", action="store_true", help="Validate experiment inputs and runtime without inference.")
    parser.add_argument("--resume", action="store_true", help="Append results and skip image-mode jobs that already succeeded.")
    parser.add_argument("--limit-jobs", type=int, help="Process at most this many image-mode jobs in the current run.")
    args = parser.parse_args()
    if args.limit_jobs is not None and args.limit_jobs < 1:
        parser.error("--limit-jobs must be greater than 0.")

    try:
        anyio.run(
            run_batch,
            BatchRunConfig(
                images_dir=args.images_dir,
                annotations_path=args.annotations,
                predictions_path=args.predictions,
                evaluation_path=args.output,
                modes=tuple(args.modes),
                allow_mock=args.allow_mock,
                preflight_only=args.preflight_only,
                resume=args.resume,
                limit_jobs=args.limit_jobs,
            ),
        )
    except ExperimentPreflightError as exc:
        print("Experiment preflight failed:")
        for error in exc.errors:
            print(f"- {error}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
