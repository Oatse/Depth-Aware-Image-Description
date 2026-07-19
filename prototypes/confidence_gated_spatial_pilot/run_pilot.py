from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from app.config import Settings
from models.depth_anything import DepthAnything
from prototypes.confidence_gated_spatial_pilot.gating import (
    SpatialObservation,
    decide_gate,
    selective_risk,
)
from services.depth_analysis import analyze_depth_regions


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = Path(__file__).with_name("protocol.json")
DEFAULT_OUTPUT_DIR = ROOT / "results" / "prototypes" / "confidence_gated_spatial_pilot_20260718"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def read_protocol() -> dict[str, Any]:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def transformed_images(image: Image.Image) -> list[tuple[str, Image.Image]]:
    rgb = image.convert("RGB")
    jpeg_buffer = io.BytesIO()
    rgb.save(jpeg_buffer, format="JPEG", quality=40)
    jpeg_buffer.seek(0)
    jpeg = Image.open(jpeg_buffer).convert("RGB")
    return [
        ("original", rgb.copy()),
        ("brightness_0.60", ImageEnhance.Brightness(rgb).enhance(0.60)),
        ("brightness_1.40", ImageEnhance.Brightness(rgb).enhance(1.40)),
        ("gaussian_blur_radius_2.0", rgb.filter(ImageFilter.GaussianBlur(radius=2.0))),
        ("jpeg_quality_40", jpeg.copy()),
    ]


def dataset_rows(protocol: dict[str, Any]) -> Iterable[tuple[int, dict[str, Any]]]:
    from datasets import load_dataset

    dataset = protocol["dataset"]
    source = (
        "hf://datasets/"
        f"{dataset['repository']}@{dataset['revision']}/"
        f"{dataset['source_file']}"
    )
    stream = load_dataset(
        "parquet",
        data_files=source,
        split="train",
        streaming=True,
    )
    wanted = set(dataset["sample_indices"])
    for index, row in enumerate(stream):
        if index in wanted:
            yield index, row
        if index >= max(wanted):
            break


def observation_from_summary(summary: dict[str, Any]) -> SpatialObservation:
    nearest_region = str(summary["nearest_region"])
    return SpatialObservation(
        nearest_region=nearest_region,
        distance_category=str(summary["distance_category"]),
        nearest_score=float(summary["regions"][nearest_region]["score"]),
    )


def save_depth_visual(depth: np.ndarray, path: Path) -> None:
    finite = np.asarray(depth, dtype=np.float32)
    valid = finite[np.isfinite(finite)]
    if valid.size == 0:
        visual = np.zeros(finite.shape, dtype=np.uint8)
    else:
        low, high = np.percentile(valid, [1, 99])
        span = max(float(high - low), 1e-8)
        visual = np.clip((finite - low) / span, 0.0, 1.0)
        visual = (visual * 255).astype(np.uint8)
    Image.fromarray(visual).save(path)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def accuracy(values: Iterable[bool]) -> float:
    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else 0.0


def build_report(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    gates = summary["feasibility_gate_results"]
    lines = [
        "# Confidence-Gated Spatial Description Pilot",
        "",
        f"Pilot ID: `{summary['pilot_id']}`",
        f"Decision: **{summary['decision']}**",
        "",
        "## Mechanical result",
        "",
        f"- Samples: {summary['sample_count']}",
        f"- Depth calls: {summary['successful_depth_calls']}/{summary['expected_depth_calls']}",
        f"- Total inference time: {summary['total_inference_seconds']:.3f} s",
        f"- Always-fuse joint accuracy: {metrics['always_fuse']['joint_claim_accuracy']:.4f}",
        f"- Always-fuse selective risk: {metrics['always_fuse']['selective_risk']:.4f}",
        f"- Confidence-gated coverage: {metrics['confidence_gated']['coverage']:.4f}",
        f"- Confidence-gated selective risk: {metrics['confidence_gated']['selective_risk']}",
        "",
        "## Frozen feasibility gates",
        "",
    ]
    for name, result in gates.items():
        lines.append(f"- `{name}`: {'PASS' if result else 'FAIL'}")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "This six-sample run is a feasibility pilot only. It cannot establish generalization, statistical superiority, or object-specific distance grounding. A final experiment requires a separate calibration split, held-out test split, and a new frozen protocol.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    protocol = read_protocol()
    output_dir = args.output_dir.resolve()
    samples_dir = output_dir / "samples"
    output_dir.mkdir(parents=True, exist_ok=True)
    samples_dir.mkdir(parents=True, exist_ok=True)

    protocol_copy = output_dir / "frozen_protocol.json"
    protocol_copy.write_text(
        json.dumps(protocol, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    settings = Settings(save_depth_map=False)
    depth_model = DepthAnything(settings)
    model_path = depth_model._find_onnx_model()
    if model_path is None:
        raise SystemExit(f"Depth model was not found at {settings.depth_model_path}")

    gate = protocol["gate"]
    expected_transforms = protocol["transforms"]
    call_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    total_inference_seconds = 0.0
    successful_calls = 0

    for sample_index, row in dataset_rows(protocol):
        image = row["image"].convert("RGB")
        ground_truth_depth = np.asarray(row["depth_map"], dtype=np.float32)
        if ground_truth_depth.shape != (image.height, image.width):
            raise ValueError(
                f"Sample {sample_index} is not aligned: RGB {image.size}, depth {ground_truth_depth.shape}."
            )

        image.save(samples_dir / f"sample_{sample_index:03d}_rgb.jpg", quality=90)
        save_depth_visual(
            ground_truth_depth,
            samples_dir / f"sample_{sample_index:03d}_gt_depth.png",
        )

        ground_truth_summary = analyze_depth_regions(ground_truth_depth)
        observations: list[SpatialObservation] = []
        transformations = transformed_images(image)
        if [name for name, _ in transformations] != expected_transforms:
            raise ValueError("Runtime transformations do not match the frozen protocol.")

        for transform_name, transformed in transformations:
            result = depth_model.estimate(
                transformed,
                f"nyuv2_{sample_index}_{transform_name}.jpg",
            )
            total_inference_seconds += result.latency_ms / 1000.0
            if not result.success or result.depth_map is None:
                call_rows.append(
                    {
                        "sample_index": sample_index,
                        "transform": transform_name,
                        "success": False,
                        "latency_ms": result.latency_ms,
                        "predicted_nearest_region": "",
                        "predicted_distance_category": "",
                        "predicted_nearest_score": "",
                        "error": result.error or "unknown_error",
                    }
                )
                continue

            successful_calls += 1
            predicted_summary = analyze_depth_regions(result.depth_map)
            observation = observation_from_summary(predicted_summary)
            observations.append(observation)
            call_rows.append(
                {
                    "sample_index": sample_index,
                    "transform": transform_name,
                    "success": True,
                    "latency_ms": result.latency_ms,
                    "predicted_nearest_region": observation.nearest_region,
                    "predicted_distance_category": observation.distance_category,
                    "predicted_nearest_score": round(observation.nearest_score, 6),
                    "error": "",
                }
            )

        if len(observations) != len(expected_transforms):
            continue

        decision = decide_gate(
            observations,
            minimum_nearest_region_agreement=gate["minimum_nearest_region_agreement"],
            minimum_distance_category_agreement=gate["minimum_distance_category_agreement"],
            maximum_relative_mad=gate["maximum_relative_mad"],
        )
        original = observations[0]
        gt_region = str(ground_truth_summary["nearest_region"])
        gt_category = str(ground_truth_summary["distance_category"])
        always_correct = (
            original.nearest_region == gt_region
            and original.distance_category == gt_category
        )
        gated_correct = (
            decision.nearest_region == gt_region
            and decision.distance_category == gt_category
        )
        sample_rows.append(
            {
                "sample_index": sample_index,
                "ground_truth_nearest_region": gt_region,
                "ground_truth_distance_category": gt_category,
                "always_nearest_region": original.nearest_region,
                "always_distance_category": original.distance_category,
                "always_region_correct": original.nearest_region == gt_region,
                "always_category_correct": original.distance_category == gt_category,
                "always_joint_correct": always_correct,
                "gated_accepted": decision.accepted,
                "gated_nearest_region": decision.nearest_region,
                "gated_distance_category": decision.distance_category,
                "gated_joint_correct": gated_correct if decision.accepted else "",
                "nearest_region_agreement": round(decision.nearest_region_agreement, 6),
                "distance_category_agreement": round(decision.distance_category_agreement, 6),
                "relative_mad": round(decision.relative_mad, 6),
                "rejection_reasons": "|".join(decision.reasons),
            }
        )

    expected_samples = protocol["dataset"]["sample_size"]
    expected_calls = expected_samples * len(expected_transforms)
    if len(sample_rows) != expected_samples:
        raise RuntimeError(
            f"Expected {expected_samples} complete samples, received {len(sample_rows)}."
        )

    accepted_rows = [row for row in sample_rows if row["gated_accepted"]]
    always_correctness = [bool(row["always_joint_correct"]) for row in sample_rows]
    gated_correctness = [bool(row["gated_joint_correct"]) for row in accepted_rows]
    gated_coverage = len(accepted_rows) / len(sample_rows)
    always_risk = selective_risk(always_correctness)
    gated_risk = selective_risk(gated_correctness)

    metrics = {
        "no_depth": {"coverage": 0.0, "selective_risk": None},
        "always_fuse": {
            "coverage": 1.0,
            "nearest_region_accuracy": accuracy(
                bool(row["always_region_correct"]) for row in sample_rows
            ),
            "distance_category_accuracy": accuracy(
                bool(row["always_category_correct"]) for row in sample_rows
            ),
            "joint_claim_accuracy": accuracy(always_correctness),
            "selective_risk": always_risk,
        },
        "confidence_gated": {
            "coverage": gated_coverage,
            "joint_claim_accuracy_at_coverage": accuracy(gated_correctness),
            "selective_risk": gated_risk,
        },
    }

    feasibility = protocol["feasibility_gates"]
    gate_results = {
        "all_depth_calls_succeeded": successful_calls == expected_calls,
        "coverage_is_non_degenerate": (
            feasibility["minimum_gated_coverage"]
            <= gated_coverage
            <= feasibility["maximum_gated_coverage"]
        ),
        "gated_risk_not_worse_than_always_fuse": (
            gated_risk is not None
            and always_risk is not None
            and gated_risk <= always_risk
        ),
        "inference_time_within_budget": (
            total_inference_seconds <= feasibility["maximum_total_inference_seconds"]
        ),
    }
    decision = (
        "PROCEED_TO_CALIBRATION_PILOT"
        if all(gate_results.values())
        else "REVISE_OR_REJECT"
    )
    summary = {
        "pilot_id": protocol["pilot_id"],
        "decision": decision,
        "sample_count": len(sample_rows),
        "expected_depth_calls": expected_calls,
        "successful_depth_calls": successful_calls,
        "total_inference_seconds": round(total_inference_seconds, 6),
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "model_sha256": sha256_file(model_path),
        "model_path": str(model_path.resolve()),
        "metrics": metrics,
        "feasibility_gate_results": gate_results,
        "gate_configuration": gate,
        "sample_decisions": [
            {
                "sample_index": row["sample_index"],
                "accepted": row["gated_accepted"],
                "rejection_reasons": row["rejection_reasons"],
            }
            for row in sample_rows
        ],
    }

    write_csv(output_dir / "inference_calls.csv", call_rows)
    write_csv(output_dir / "sample_decisions.csv", sample_rows)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "REPORT.md").write_text(build_report(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if decision == "PROCEED_TO_CALIBRATION_PILOT" else 2


if __name__ == "__main__":
    raise SystemExit(main())

