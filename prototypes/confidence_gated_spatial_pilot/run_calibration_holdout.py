from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from app.config import Settings
from models.depth_anything import DepthAnything
from prototypes.confidence_gated_spatial_pilot.calibration import (
    PreparedSample,
    candidate_configs,
    decision_for_sample,
    evaluate_config,
    joint_correct,
    paired_risk_difference_interval,
    select_config,
)
from prototypes.confidence_gated_spatial_pilot.gating import SpatialObservation, selective_risk
from prototypes.confidence_gated_spatial_pilot.run_pilot import (
    ROOT,
    save_depth_visual,
    sha256_file,
    transformed_images,
)
from services.depth_analysis import analyze_depth_regions


PROTOCOL_PATH = Path(__file__).with_name("calibration_holdout_protocol.json")
DEFAULT_OUTPUT_DIR = ROOT / "results" / "prototypes" / "confidence_gated_spatial_calibration_holdout_20260718"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_selected_rows(protocol: dict[str, Any]) -> dict[int, dict[str, Any]]:
    from datasets import load_dataset

    dataset = protocol["dataset"]
    selected_indices = set(dataset["calibration_indices"] + dataset["holdout_indices"])
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
    selected: dict[int, dict[str, Any]] = {}
    maximum_index = max(selected_indices)
    for index, row in enumerate(stream):
        if index in selected_indices:
            selected[index] = row
            print(f"loaded dataset sample {index} ({len(selected)}/{len(selected_indices)})", flush=True)
        if index >= maximum_index:
            break
    missing = selected_indices.difference(selected)
    if missing:
        raise RuntimeError(f"Dataset indices were not found: {sorted(missing)}")
    return selected


def observation_from_summary(summary: dict[str, Any]) -> SpatialObservation:
    nearest_region = str(summary["nearest_region"])
    return SpatialObservation(
        nearest_region=nearest_region,
        distance_category=str(summary["distance_category"]),
        nearest_score=float(summary["regions"][nearest_region]["score"]),
    )


def process_split(
    split_name: str,
    indices: list[int],
    rows: dict[int, dict[str, Any]],
    depth_model: DepthAnything,
    expected_transforms: list[str],
    samples_dir: Path,
) -> tuple[list[PreparedSample], list[dict[str, Any]], int, float]:
    prepared: list[PreparedSample] = []
    calls: list[dict[str, Any]] = []
    successes = 0
    inference_seconds = 0.0
    for position, sample_index in enumerate(indices, start=1):
        row = rows[sample_index]
        image = row["image"].convert("RGB")
        ground_truth_depth = np.asarray(row["depth_map"], dtype=np.float32)
        if ground_truth_depth.shape != (image.height, image.width):
            raise ValueError(
                f"Sample {sample_index} is not aligned: RGB {image.size}, depth {ground_truth_depth.shape}."
            )
        image.save(samples_dir / f"{split_name}_{sample_index:03d}_rgb.jpg", quality=90)
        save_depth_visual(
            ground_truth_depth,
            samples_dir / f"{split_name}_{sample_index:03d}_gt_depth.png",
        )
        ground_truth_summary = analyze_depth_regions(ground_truth_depth)
        transformations = transformed_images(image)
        if [name for name, _ in transformations] != expected_transforms:
            raise ValueError("Runtime transformations do not match the frozen protocol.")
        observations: list[SpatialObservation] = []
        for transform_name, transformed in transformations:
            result = depth_model.estimate(
                transformed,
                f"nyuv2_{split_name}_{sample_index}_{transform_name}.jpg",
            )
            inference_seconds += result.latency_ms / 1000.0
            if not result.success or result.depth_map is None:
                calls.append(
                    {
                        "split": split_name,
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
            successes += 1
            predicted_summary = analyze_depth_regions(result.depth_map)
            observation = observation_from_summary(predicted_summary)
            observations.append(observation)
            calls.append(
                {
                    "split": split_name,
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
            raise RuntimeError(f"Sample {sample_index} has incomplete depth observations.")
        prepared.append(
            PreparedSample(
                sample_index=sample_index,
                ground_truth_nearest_region=str(ground_truth_summary["nearest_region"]),
                ground_truth_distance_category=str(ground_truth_summary["distance_category"]),
                observations=tuple(observations),
            )
        )
        print(f"{split_name} inference {position}/{len(indices)} complete", flush=True)
    return prepared, calls, successes, inference_seconds


def calibration_rows(evaluations: Iterable[Any]) -> list[dict[str, Any]]:
    return [
        {
            **asdict(evaluation.config),
            "coverage": evaluation.coverage,
            "selective_risk": evaluation.selective_risk,
            "accepted_count": evaluation.accepted_count,
            "correct_accepted_count": evaluation.correct_accepted_count,
        }
        for evaluation in evaluations
    ]


def heldout_decision_rows(samples: list[PreparedSample], selected: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sample in samples:
        original = sample.observations[0]
        decision = decision_for_sample(sample, selected.config)
        always_correct = joint_correct(
            original.nearest_region,
            original.distance_category,
            sample,
        )
        gated_correct = joint_correct(
            decision.nearest_region,
            decision.distance_category,
            sample,
        )
        rows.append(
            {
                "sample_index": sample.sample_index,
                "ground_truth_nearest_region": sample.ground_truth_nearest_region,
                "ground_truth_distance_category": sample.ground_truth_distance_category,
                "always_nearest_region": original.nearest_region,
                "always_distance_category": original.distance_category,
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
    return rows


def rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def report_text(summary: dict[str, Any]) -> str:
    calibration = summary["calibration"]
    heldout = summary["heldout"]
    gates = summary["feasibility_gate_results"]
    interval = heldout["risk_difference_bootstrap_interval"]
    return "\n".join(
        [
            "# Confidence-Gated Spatial Calibration and Held-Out Pilot",
            "",
            f"Run ID: `{summary['run_id']}`",
            f"Decision: **{summary['decision']}**",
            "",
            "## Calibration",
            "",
            f"- Samples: {calibration['sample_count']}",
            f"- Selected configuration: `{json.dumps(calibration['selected_config'], sort_keys=True)}`",
            f"- Selected coverage: {calibration['coverage']:.4f}",
            f"- Selected risk: {calibration['selective_risk']:.4f}",
            "",
            "## Held-out",
            "",
            f"- Samples: {heldout['sample_count']}",
            f"- Always-fuse joint accuracy: {heldout['always_fuse_joint_accuracy']:.4f}",
            f"- Always-fuse risk: {heldout['always_fuse_risk']:.4f}",
            f"- Gated coverage: {heldout['gated_coverage']:.4f}",
            f"- Gated accuracy at coverage: {heldout['gated_joint_accuracy_at_coverage']:.4f}",
            f"- Gated risk: {heldout['gated_risk']:.4f}",
            f"- Gated minus always risk: {heldout['risk_difference']:.4f}",
            f"- Bootstrap snapshot interval: {interval}",
            f"- Error capture: {heldout['captured_errors']}/{heldout['always_fuse_errors']}",
            f"- False rejection rate: {heldout['false_rejection_rate']}",
            "",
            "## Frozen gates",
            "",
            *[
                f"- `{name}`: {'PASS' if value else 'FAIL'}"
                for name, value in gates.items()
            ],
            "",
            "## Boundary",
            "",
            "This is a calibration and held-out feasibility run. It is not scene-stratified, does not invoke a VLM, and does not establish thesis-level superiority or object-specific distance grounding.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    output_dir = args.output_dir.resolve()
    samples_dir = output_dir / "samples"
    output_dir.mkdir(parents=True, exist_ok=True)
    samples_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "frozen_protocol.json").write_text(
        json.dumps(protocol, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    started_at = time.perf_counter()
    rows = load_selected_rows(protocol)
    settings = Settings(save_depth_map=False)
    depth_model = DepthAnything(settings)
    model_path = depth_model._find_onnx_model()
    if model_path is None:
        raise SystemExit(f"Depth model was not found at {settings.depth_model_path}")

    expected_transforms = protocol["transforms"]
    calibration_samples, calibration_calls, calibration_successes, calibration_seconds = process_split(
        "calibration",
        protocol["dataset"]["calibration_indices"],
        rows,
        depth_model,
        expected_transforms,
        samples_dir,
    )
    configs = candidate_configs(protocol["candidate_grid"])
    evaluations = [evaluate_config(calibration_samples, config) for config in configs]
    objective = protocol["selection_objective"]
    selected = select_config(
        evaluations,
        minimum_coverage=objective["minimum_calibration_coverage"],
        maximum_coverage=objective["maximum_calibration_coverage"],
    )
    selected_payload = {
        "run_id": protocol["run_id"],
        "selected_config": asdict(selected.config),
        "calibration_coverage": selected.coverage,
        "calibration_selective_risk": selected.selective_risk,
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
    }
    (output_dir / "frozen_holdout_gate.json").write_text(
        json.dumps(selected_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv(output_dir / "calibration_candidates.csv", calibration_rows(evaluations))
    write_csv(output_dir / "calibration_inference_calls.csv", calibration_calls)
    print(f"holdout gate frozen: {selected_payload['selected_config']}", flush=True)

    holdout_samples, holdout_calls, holdout_successes, holdout_seconds = process_split(
        "holdout",
        protocol["dataset"]["holdout_indices"],
        rows,
        depth_model,
        expected_transforms,
        samples_dir,
    )
    decisions = heldout_decision_rows(holdout_samples, selected)
    write_csv(output_dir / "holdout_inference_calls.csv", holdout_calls)
    write_csv(output_dir / "holdout_decisions.csv", decisions)

    always_correctness = [bool(row["always_joint_correct"]) for row in decisions]
    accepted = [row for row in decisions if row["gated_accepted"]]
    gated_correctness = [bool(row["gated_joint_correct"]) for row in accepted]
    always_risk = selective_risk(always_correctness)
    gated_risk = selective_risk(gated_correctness)
    if always_risk is None or gated_risk is None:
        raise RuntimeError("Held-out risk could not be computed.")
    always_errors = sum(not value for value in always_correctness)
    captured_errors = sum(
        not bool(row["always_joint_correct"]) and not bool(row["gated_accepted"])
        for row in decisions
    )
    always_correct_count = sum(always_correctness)
    false_rejections = sum(
        bool(row["always_joint_correct"]) and not bool(row["gated_accepted"])
        for row in decisions
    )
    gated_coverage = len(accepted) / len(decisions)
    paired_rows = [
        (
            bool(row["always_joint_correct"]),
            bool(row["gated_accepted"]),
            bool(row["gated_joint_correct"]) if row["gated_accepted"] else False,
        )
        for row in decisions
    ]
    bootstrap = protocol["bootstrap"]
    interval = paired_risk_difference_interval(
        paired_rows,
        resamples=bootstrap["resamples"],
        seed=bootstrap["seed"],
        confidence_level=bootstrap["confidence_level"],
    )
    total_inference_seconds = calibration_seconds + holdout_seconds
    successful_calls = calibration_successes + holdout_successes
    expected_calls = (
        len(protocol["dataset"]["calibration_indices"])
        + len(protocol["dataset"]["holdout_indices"])
    ) * len(expected_transforms)
    heldout_gates = protocol["heldout_feasibility_gates"]
    false_rejection_rate = rate(false_rejections, always_correct_count)
    gate_results = {
        "all_depth_calls_succeeded": successful_calls == expected_calls,
        "heldout_coverage_is_non_degenerate": (
            heldout_gates["minimum_coverage"]
            <= gated_coverage
            <= heldout_gates["maximum_coverage"]
        ),
        "heldout_gated_risk_not_worse_than_always_fuse": gated_risk <= always_risk,
        "captured_at_least_one_always_fuse_error": (
            captured_errors >= heldout_gates["minimum_captured_always_fuse_errors"]
        ),
        "false_rejection_rate_within_limit": (
            false_rejection_rate is not None
            and false_rejection_rate <= heldout_gates["maximum_false_rejection_rate"]
        ),
        "inference_time_within_budget": (
            total_inference_seconds <= heldout_gates["maximum_total_inference_seconds"]
        ),
    }
    decision = (
        "PROCEED_TO_FINAL_PROTOCOL_DESIGN"
        if all(gate_results.values())
        else "STOP_OR_REDESIGN_GATE"
    )
    summary = {
        "run_id": protocol["run_id"],
        "decision": decision,
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "model_sha256": sha256_file(model_path),
        "successful_depth_calls": successful_calls,
        "expected_depth_calls": expected_calls,
        "total_inference_seconds": round(total_inference_seconds, 6),
        "total_wall_seconds": round(time.perf_counter() - started_at, 6),
        "calibration": {
            "sample_count": len(calibration_samples),
            "candidate_count": len(evaluations),
            "selected_config": asdict(selected.config),
            "coverage": selected.coverage,
            "selective_risk": selected.selective_risk,
        },
        "heldout": {
            "sample_count": len(decisions),
            "always_fuse_joint_accuracy": 1.0 - always_risk,
            "always_fuse_risk": always_risk,
            "gated_coverage": gated_coverage,
            "gated_joint_accuracy_at_coverage": 1.0 - gated_risk,
            "gated_risk": gated_risk,
            "risk_difference": gated_risk - always_risk,
            "risk_difference_bootstrap_interval": interval,
            "always_fuse_errors": always_errors,
            "captured_errors": captured_errors,
            "error_capture_rate": rate(captured_errors, always_errors),
            "always_fuse_correct": always_correct_count,
            "false_rejections": false_rejections,
            "false_rejection_rate": false_rejection_rate,
        },
        "feasibility_gate_results": gate_results,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "REPORT.md").write_text(report_text(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if decision == "PROCEED_TO_FINAL_PROTOCOL_DESIGN" else 2


if __name__ == "__main__":
    raise SystemExit(main())

