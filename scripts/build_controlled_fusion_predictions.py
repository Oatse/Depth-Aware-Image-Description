import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from models.depth_anything import DepthAnything
from models.fusion import fuse_description
from models.fusion_types import FusionPolicy
from services.depth_analysis import analyze_depth_regions
from services.image_preprocess import preprocess_image
from services.result_logger import PREDICTION_FIELDS


CONTROLLED_FIELDS: Final = [
    *PREDICTION_FIELDS,
    "source_modes",
    "latency_basis",
]
IMAGE_EXTENSIONS: Final = frozenset({".jpg", ".jpeg", ".png", ".webp"})


@dataclass(frozen=True, slots=True)
class ControlledFusionInputError(ValueError):
    message: str

    def __str__(self) -> str:
        return self.message


def build_controlled_fusion_rows(
    gemma_prediction: dict[str, str],
    depth_summary: dict,
    depth_latency_ms: int,
) -> list[dict[str, str | int]]:
    if (
        gemma_prediction.get("mode") != "gemma_only"
        or gemma_prediction.get("error")
        or not gemma_prediction.get("description_gemma", "").strip()
    ):
        raise ControlledFusionInputError("controlled fusion requires a successful gemma_only prediction")

    structured = {
        "description": gemma_prediction.get("description_gemma", ""),
        "main_object": gemma_prediction.get("main_object", ""),
        "object_position": gemma_prediction.get("object_position", ""),
        "scene_type": gemma_prediction.get("scene_type", ""),
    }
    common = {
        "timestamp": "",
        "image_name": gemma_prediction.get("image_name", ""),
        "description_gemma": gemma_prediction.get("description_gemma", ""),
        "main_object": gemma_prediction.get("main_object", ""),
        "object_position": gemma_prediction.get("object_position", ""),
        "scene_type": gemma_prediction.get("scene_type", ""),
        "nearest_region": str(depth_summary.get("nearest_region", "")),
        "distance_category": str(depth_summary.get("distance_category", "")),
        "estimated_distance": str(depth_summary.get("estimated_distance", "")),
        "gemma_latency_ms": gemma_prediction.get("gemma_latency_ms", "0"),
        "depth_latency_ms": depth_latency_ms,
        "total_latency_ms": _integer_value(gemma_prediction.get("gemma_latency_ms", "0")) + depth_latency_ms,
        "error": "",
        "safe_direction": str(depth_summary.get("safe_direction", "")),
        "source_modes": "gemma_only+shared_depth",
        "latency_basis": "component_inference_sum",
    }
    rows: list[dict[str, str | int]] = []
    for mode, policy in (
        ("gemma_depth_legacy_controlled", FusionPolicy.LEGACY_VERBOSE),
        ("gemma_depth_constrained_controlled", FusionPolicy.EVIDENCE_CONSTRAINED),
    ):
        fusion = fuse_description(
            gemma_prediction.get("description_gemma"),
            depth_summary,
            "gemma_depth",
            structured,
            policy=policy,
        )
        rows.append({
            **common,
            "mode": mode,
            "final_description": fusion["final_description"],
            "fusion_policy": policy.value,
        })
    return rows


def build_controlled_file(images_dir: Path, predictions_path: Path, output_path: Path) -> None:
    gemma_predictions = {
        row.get("image_name", ""): row
        for row in _read_csv(predictions_path)
        if row.get("mode") == "gemma_only" and not row.get("error")
    }
    settings = get_settings().model_copy(update={"save_depth_map": False})
    depth_model = DepthAnything(settings)
    image_paths = sorted(
        path
        for path in images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CONTROLLED_FIELDS)
        writer.writeheader()
        for image_path in image_paths:
            gemma_prediction = gemma_predictions.get(image_path.name)
            if gemma_prediction is None:
                raise ControlledFusionInputError(f"missing gemma_only prediction for {image_path.name}")
            processed = preprocess_image(image_path.read_bytes(), settings.image_max_dimension)
            depth_result = depth_model.estimate(processed.image, image_path.name)
            if not depth_result.success:
                raise ControlledFusionInputError(
                    f"depth inference failed for {image_path.name}: {depth_result.error or 'unknown error'}"
                )
            depth_summary = analyze_depth_regions(depth_result.depth_map)
            writer.writerows(build_controlled_fusion_rows(
                gemma_prediction,
                depth_summary,
                depth_result.latency_ms,
            ))
            handle.flush()
            print(f"{image_path.name} | controlled fusion complete")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _integer_value(value: str) -> int:
    try:
        return int(float(value))
    except ValueError:
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build controlled legacy and evidence-constrained fusion rows from one shared Gemma branch."
    )
    parser.add_argument("--images-dir", type=Path, default=Path("dataset/final_images"))
    parser.add_argument("--predictions", type=Path, default=Path("results/final_predictions_active_20260714.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/controlled_fusion_predictions.csv"))
    args = parser.parse_args()
    build_controlled_file(args.images_dir, args.predictions, args.output)


if __name__ == "__main__":
    main()
