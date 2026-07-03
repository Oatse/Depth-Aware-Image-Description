import argparse
import asyncio
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from models.depth_anything import DepthAnything
from models.gemma_client import GemmaClient
from services.evaluator import evaluate_predictions
from services.pipeline import analyze_image_bytes, prediction_row
from services.result_logger import PREDICTION_FIELDS


DEFAULT_MODES = ("gemma_only", "gemma_depth")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


async def run_batch(
    images_dir: Path,
    annotations_path: Path,
    predictions_path: Path,
    evaluation_path: Path,
    modes: tuple[str, ...],
) -> None:
    settings = get_settings()
    gemma_client = GemmaClient(settings)
    depth_model = DepthAnything(settings)
    image_paths = sorted(path for path in images_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)

    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    with predictions_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREDICTION_FIELDS)
        writer.writeheader()
        for image_path in image_paths:
            image_bytes = image_path.read_bytes()
            for mode in modes:
                result = await analyze_image_bytes(
                    image_bytes=image_bytes,
                    filename=image_path.name,
                    mode=mode,
                    settings=settings,
                    gemma_client=gemma_client,
                    depth_model=depth_model,
                )
                writer.writerow(prediction_row(result))
                print(f"{image_path.name} | {mode} | success={result.success} | error={result.error or '-'}")

    summary = evaluate_predictions(annotations_path, predictions_path, evaluation_path)
    print("Evaluation Summary:")
    print(f"- Total images: {summary.total_images}")
    print(f"- Object accuracy: {summary.object_accuracy:.2%}")
    print(f"- Position accuracy: {summary.position_accuracy:.2%}")
    print(f"- Distance category accuracy: {summary.distance_category_accuracy:.2%}")
    print(f"- Obstacle warning accuracy: {summary.obstacle_warning_accuracy:.2%}")
    print(f"- Description quality: {summary.description_quality:.2f}/5")
    print(f"- Average latency: {summary.average_latency_ms:.1f} ms")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Gemma-only and Gemma+Depth batch evaluation.")
    parser.add_argument("--images-dir", type=Path, default=Path("dataset/images"))
    parser.add_argument("--annotations", type=Path, default=Path("dataset/annotations.csv"))
    parser.add_argument("--predictions", type=Path, default=Path("results/predictions.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/evaluation.csv"))
    parser.add_argument("--modes", nargs="+", choices=["gemma_only", "depth_only", "gemma_depth"], default=list(DEFAULT_MODES))
    args = parser.parse_args()

    asyncio.run(
        run_batch(
            images_dir=args.images_dir,
            annotations_path=args.annotations,
            predictions_path=args.predictions,
            evaluation_path=args.output,
            modes=tuple(args.modes),
        )
    )


if __name__ == "__main__":
    main()
