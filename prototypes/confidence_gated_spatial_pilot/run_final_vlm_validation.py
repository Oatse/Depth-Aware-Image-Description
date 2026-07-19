from __future__ import annotations

import argparse
import asyncio
import base64
import csv
import hashlib
import io
import json
import statistics
import time
from pathlib import Path
from typing import Any

import httpx
import numpy as np
from PIL import Image

from app.config import Settings
from models.fusion import fuse_description
from models.gemma_client import GemmaClient, GemmaClientError
from services.image_preprocess import preprocess_image


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = Path(__file__).with_name("final_vlm_protocol.json")
SOURCE_DIR = ROOT / "results" / "prototypes" / "confidence_gated_spatial_calibration_holdout_20260718"
DEFAULT_OUTPUT_DIR = ROOT / "results" / "prototypes" / "confidence_gated_vlm_validation_20260718"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--protocol", type=Path, default=PROTOCOL_PATH)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_base64(path: Path) -> str:
    raw = path.read_bytes()
    processed = preprocess_image(raw, 768)
    return processed.base64_image


def json_signature(structured: dict[str, Any] | None, description: str) -> str:
    payload = {
        "structured": structured or {},
        "description": " ".join(description.split()),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def build_depth_summary(row: dict[str, str]) -> dict[str, str] | None:
    if row["gated_accepted"].lower() != "true":
        return None
    return {
        "nearest_region": row["gated_nearest_region"],
        "distance_category": row["gated_distance_category"],
    }


async def check_model(settings: Settings) -> tuple[int, str]:
    endpoint = settings.lm_studio_openai_base_url + "/models"
    async with httpx.AsyncClient(timeout=settings.lm_studio_health_timeout) as client:
        response = await client.get(endpoint)
        response.raise_for_status()
        data = response.json()
    model_ids = [item.get("id") for item in data.get("data", []) if isinstance(item, dict)]
    return response.status_code, json.dumps(model_ids, ensure_ascii=False)


async def run_validation(output_dir: Path, protocol_path: Path = PROTOCOL_PATH) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    source_rows = read_csv(SOURCE_DIR / "holdout_decisions.csv")
    expected_indices = [str(index) for index in protocol["dataset"]["indices"]]
    by_index = {row["sample_index"]: row for row in source_rows}
    if sorted(by_index) != sorted(expected_indices):
        raise RuntimeError("Held-out decision rows do not match the frozen final protocol.")

    settings = Settings(lm_studio_model=protocol["vlm"]["model"])
    status_code, model_ids = await check_model(settings)
    client = GemmaClient(settings)
    rows: list[dict[str, Any]] = []
    latencies: list[int] = []
    structured_successes = 0
    vlm_successes = 0
    pair_identity_failures = 0
    errors: list[dict[str, str]] = []

    for position, index in enumerate(expected_indices, start=1):
        source = by_index[index]
        image_path = SOURCE_DIR / "samples" / f"holdout_{int(index):03d}_rgb.jpg"
        started_at = time.perf_counter()
        try:
            result = await client.describe_image(image_base64(image_path))
            vlm_successes += 1
            latencies.append(result.latency_ms)
            if result.structured is not None:
                structured_successes += 1
            baseline = fuse_description(
                result.description,
                None,
                "gemma_only",
                result.structured,
            )
            gated = fuse_description(
                result.description,
                build_depth_summary(source),
                "gemma_depth",
                result.structured,
            )
            baseline_signature = json_signature(result.structured, result.description)
            gated_visual_signature = json_signature(result.structured, result.description)
            if baseline_signature != gated_visual_signature:
                pair_identity_failures += 1
            rows.append(
                {
                    "sample_index": index,
                    "image_path": str(image_path),
                    "gated_accepted": source["gated_accepted"],
                    "ground_truth_nearest_region": source["ground_truth_nearest_region"],
                    "ground_truth_distance_category": source["ground_truth_distance_category"],
                    "gated_nearest_region": source["gated_nearest_region"],
                    "gated_distance_category": source["gated_distance_category"],
                    "gated_depth_joint_correct": source["gated_joint_correct"],
                    "structured_json": json.dumps(result.structured or {}, ensure_ascii=False),
                    "description_gemma": result.description,
                    "baseline_description": baseline["final_description"],
                    "gated_description": gated["final_description"],
                    "gated_added_depth_claim": baseline["final_description"] != gated["final_description"],
                    "latency_ms": result.latency_ms,
                    "wall_seconds": round(time.perf_counter() - started_at, 6),
                    "error": "",
                    "raw_response": result.raw_response,
                }
            )
        except (GemmaClientError, OSError, ValueError, httpx.HTTPError) as exc:
            errors.append({"sample_index": index, "error": str(exc)})
            rows.append(
                {
                    "sample_index": index,
                    "image_path": str(image_path),
                    "gated_accepted": source["gated_accepted"],
                    "ground_truth_nearest_region": source["ground_truth_nearest_region"],
                    "ground_truth_distance_category": source["ground_truth_distance_category"],
                    "gated_nearest_region": source["gated_nearest_region"],
                    "gated_distance_category": source["gated_distance_category"],
                    "gated_depth_joint_correct": source["gated_joint_correct"],
                    "structured_json": "",
                    "description_gemma": "",
                    "baseline_description": "",
                    "gated_description": "",
                    "gated_added_depth_claim": False,
                    "latency_ms": 0,
                    "wall_seconds": round(time.perf_counter() - started_at, 6),
                    "error": str(exc),
                    "raw_response": "",
                }
            )
        print(f"VLM validation {position}/{len(expected_indices)} complete", flush=True)

    repeat_rows: list[dict[str, Any]] = []
    repeat_variations = 0
    for index in protocol["repeat"]["indices"]:
        image_path = SOURCE_DIR / "samples" / f"holdout_{index:03d}_rgb.jpg"
        signatures: list[str] = []
        for repeat_number in range(protocol["repeat"]["repeats_per_index"]):
            result = await client.describe_image(image_base64(image_path))
            signatures.append(json_signature(result.structured, result.description))
            repeat_rows.append(
                {
                    "sample_index": index,
                    "repeat_number": repeat_number + 1,
                    "latency_ms": result.latency_ms,
                    "signature": signatures[-1],
                }
            )
        if len(set(signatures)) > 1:
            repeat_variations += 1

    successful_rows = [row for row in rows if not row["error"]]
    gated_rows = [row for row in successful_rows if row["gated_accepted"].lower() == "true"]
    gated_correct_rows = [row for row in gated_rows if row["gated_depth_joint_correct"].lower() == "true"]
    claimed_depth_rows = [row for row in successful_rows if row["gated_added_depth_claim"]]
    claimed_depth_correct = [row for row in claimed_depth_rows if row["gated_depth_joint_correct"].lower() == "true"]
    repeat_count = len(protocol["repeat"]["indices"])
    repeat_variation_rate = repeat_variations / repeat_count if repeat_count else None
    p50 = float(np.percentile(latencies, 50)) if latencies else None
    p95 = float(np.percentile(latencies, 95)) if latencies else None
    mean = statistics.mean(latencies) if latencies else None
    gated_coverage = len(gated_rows) / len(successful_rows) if successful_rows else 0.0
    spatial_accuracy = len(gated_correct_rows) / len(gated_rows) if gated_rows else None
    claim_accuracy = len(claimed_depth_correct) / len(claimed_depth_rows) if claimed_depth_rows else None
    gates = protocol["feasibility_gates"]
    feasibility = {
        "model_endpoint_ready": status_code == 200,
        "vlm_success_rate": vlm_successes / len(expected_indices) == gates["vlm_success_rate"],
        "structured_json_rate": (
            structured_successes / vlm_successes >= gates["structured_json_rate_minimum"]
            if vlm_successes
            else False
        ),
        "paired_same_vlm_branch_rate": pair_identity_failures == 0,
        "repeat_variation_within_limit": (
            repeat_variation_rate is not None
            and repeat_variation_rate <= gates["maximum_repeat_variation_rate"]
        ),
    }
    decision = "PROCEED_WITH_CAUTION" if all(feasibility.values()) else "REVISE_OR_BLOCK"
    summary = {
        "protocol_id": protocol["protocol_id"],
        "decision": decision,
        "source_gate_sha256": protocol["source_gate_sha256"],
        "protocol_sha256": sha256_file(protocol_path),
        "model_status_code": status_code,
        "model_ids": model_ids,
        "vlm_successes": vlm_successes,
        "expected_vlm_calls": len(expected_indices),
        "structured_successes": structured_successes,
        "structured_json_rate": structured_successes / vlm_successes if vlm_successes else 0.0,
        "latency_ms": {"mean": mean, "p50": p50, "p95": p95},
        "paired_same_vlm_branch_rate": 1.0 - (pair_identity_failures / len(expected_indices)),
        "repeat": {
            "sample_count": repeat_count,
            "variation_count": repeat_variations,
            "variation_rate": repeat_variation_rate,
        },
        "spatial": {
            "gated_depth_claim_coverage": gated_coverage,
            "gated_depth_claim_accuracy_at_coverage": spatial_accuracy,
            "gated_added_depth_claim_count": len(claimed_depth_rows),
            "gated_added_depth_claim_accuracy": claim_accuracy,
            "unsupported_gated_depth_claim_rate": (
                1.0 - claim_accuracy if claim_accuracy is not None else None
            ),
        },
        "errors": errors,
        "feasibility_gate_results": feasibility,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "vlm_predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (output_dir / "repeat_predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(repeat_rows[0]))
        writer.writeheader()
        writer.writerows(repeat_rows)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> int:
    args = parse_args()
    summary = asyncio.run(run_validation(args.output_dir.resolve(), args.protocol))
    return 0 if summary["decision"] == "PROCEED_WITH_CAUTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
