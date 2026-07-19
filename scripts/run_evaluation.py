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


def _format_optional_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2%}"


if __name__ == "__main__":
    main()
