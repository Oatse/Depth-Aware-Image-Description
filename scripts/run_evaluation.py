import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.evaluator import evaluate_predictions


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate prediction CSV against annotation CSV.")
    parser.add_argument("--annotations", type=Path, default=Path("dataset/annotations.csv"))
    parser.add_argument("--predictions", type=Path, default=Path("results/predictions.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/evaluation.csv"))
    args = parser.parse_args()

    summary = evaluate_predictions(args.annotations, args.predictions, args.output)
    print("Evaluation Summary:")
    print(f"- Total images: {summary.total_images}")
    print(f"- Object accuracy: {summary.object_accuracy:.2%}")
    print(f"- Position accuracy: {summary.position_accuracy:.2%}")
    print(f"- Distance category accuracy: {summary.distance_category_accuracy:.2%}")
    print(f"- Obstacle warning accuracy: {summary.obstacle_warning_accuracy:.2%}")
    print(f"- Description quality: {summary.description_quality:.2f}/5")
    print(f"- Average latency: {summary.average_latency_ms:.1f} ms")


if __name__ == "__main__":
    main()
