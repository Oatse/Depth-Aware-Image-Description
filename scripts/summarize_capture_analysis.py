import argparse
import csv
import json
import math
from pathlib import Path
from statistics import fmean, median, stdev
from typing import Any


def _load_jsonl_by_run_id(path: Path) -> dict[str, dict[str, Any]]:
    runs: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        run = json.loads(line)
        run_id = run.get("analysis_run_id")
        if run_id:
            runs[str(run_id)] = run
    return runs


def _error_summary(values: list[float]) -> dict[str, float]:
    return {
        "mean_error_cm": round(fmean(values), 4),
        "mae_cm": round(fmean(abs(value) for value in values), 4),
        "median_absolute_error_cm": round(median(abs(value) for value in values), 4),
        "rmse_cm": round(math.sqrt(fmean(value * value for value in values)), 4),
        "error_stddev_cm": round(stdev(values), 4) if len(values) > 1 else 0.0,
        "max_abs_error_cm": round(max(abs(value) for value in values), 4),
    }


def build_summary(
    captures_root: Path,
    manifest_path: Path,
    analysis_runs_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    runs = _load_jsonl_by_run_id(analysis_runs_path)
    rows: list[dict[str, Any]] = []

    for manifest_entry in manifest["captures"]:
        capture_id = str(manifest_entry["capture_id"])
        record_path = captures_root / "records" / f"{capture_id}.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record.get("status") != "completed":
            raise ValueError(f"Capture belum selesai dianalisis: {capture_id}")
        analysis_run_id = record.get("analysis_run_id")
        if not analysis_run_id or analysis_run_id not in runs:
            raise ValueError(f"Run analisis tidak ditemukan: {capture_id}")

        run = runs[analysis_run_id]
        if run.get("capture_id") != capture_id:
            raise ValueError(f"Capture ID pada run tidak cocok: {capture_id}")
        output = (run.get("outputs") or {}).get("sensor_assisted") or {}
        if not output.get("success"):
            raise ValueError(f"Output sensor_assisted gagal: {capture_id}")
        contribution = output.get("sensor_contribution") or {}
        if contribution.get("status") != "applied":
            raise ValueError(f"Kontribusi sensor tidak diterapkan: {capture_id}")

        ground_truth = float(manifest_entry["ground_truth_cm"])
        sensor_face_ground_truth = float(manifest_entry["sensor_face_ground_truth_cm"])
        sensor_1_raw = float(contribution["sensor_1_cm"])
        sensor_2_raw = float(contribution["sensor_2_cm"])
        sensor_1_corrected = float(contribution["sensor_1_corrected_cm"])
        sensor_2_corrected = float(contribution["sensor_2_corrected_cm"])
        frontal_reference = float(contribution["frontal_reference_cm"])
        latency = output.get("latency") or {}
        rows.append(
            {
                "capture_id": capture_id,
                "ground_truth_cm": ground_truth,
                "sensor_face_ground_truth_cm": sensor_face_ground_truth,
                "repeat_index": int(manifest_entry["repeat_index"]),
                "sensor_status": manifest_entry["sensor_status"],
                "sensor_1_raw_cm": sensor_1_raw,
                "sensor_2_raw_cm": sensor_2_raw,
                "sensor_1_raw_error_cm": round(sensor_1_raw - sensor_face_ground_truth, 4),
                "sensor_2_raw_error_cm": round(sensor_2_raw - sensor_face_ground_truth, 4),
                "pair_disagreement_cm": float(contribution["pair_disagreement_cm"]),
                "sensor_1_corrected_cm": sensor_1_corrected,
                "sensor_2_corrected_cm": sensor_2_corrected,
                "sensor_1_corrected_error_cm": round(sensor_1_corrected - ground_truth, 4),
                "sensor_2_corrected_error_cm": round(sensor_2_corrected - ground_truth, 4),
                "frontal_reference_cm": frontal_reference,
                "frontal_error_cm": round(frontal_reference - ground_truth, 4),
                "gemma_description": output.get("gemma_description"),
                "final_description": output.get("final_description"),
                "gemma_ms": latency.get("gemma_ms"),
                "total_ms": latency.get("total_ms"),
                "analysis_run_id": analysis_run_id,
                "calibration_version": contribution.get("calibration_version"),
                "image_sha256": manifest_entry["image_sha256"],
                "input_sha256": manifest_entry["input_sha256"],
            }
        )

    rows.sort(key=lambda row: (row["ground_truth_cm"], row["repeat_index"]))
    by_distance: list[dict[str, Any]] = []
    for distance in sorted({row["ground_truth_cm"] for row in rows}):
        group = [row for row in rows if row["ground_truth_cm"] == distance]
        by_distance.append(
            {
                "ground_truth_cm": distance,
                "n": len(group),
                "frontal_reference_mean_cm": round(
                    fmean(row["frontal_reference_cm"] for row in group), 4
                ),
                "frontal_error": _error_summary([row["frontal_error_cm"] for row in group]),
                "pair_disagreement_mean_cm": round(
                    fmean(row["pair_disagreement_cm"] for row in group), 4
                ),
                "total_latency_mean_ms": round(fmean(row["total_ms"] for row in group), 2),
            }
        )

    summary = {
        "schema_version": 1,
        "dataset_id": manifest["dataset_id"],
        "total_captures": len(rows),
        "completed": len(rows),
        "failed": 0,
        "overall": {
            "valid_read_rate": 1.0,
            "missing_read_count": 0,
            "sensor_1_raw_error": _error_summary(
                [row["sensor_1_raw_error_cm"] for row in rows]
            ),
            "sensor_2_raw_error": _error_summary(
                [row["sensor_2_raw_error_cm"] for row in rows]
            ),
            "sensor_1_corrected_error": _error_summary(
                [row["sensor_1_corrected_error_cm"] for row in rows]
            ),
            "sensor_2_corrected_error": _error_summary(
                [row["sensor_2_corrected_error_cm"] for row in rows]
            ),
            "frontal_error": _error_summary([row["frontal_error_cm"] for row in rows]),
            "pair_disagreement_mean_cm": round(
                fmean(row["pair_disagreement_cm"] for row in rows), 4
            ),
            "total_latency_mean_ms": round(fmean(row["total_ms"] for row in rows), 2),
        },
        "by_distance": by_distance,
    }
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Rekap hasil analisis dataset capture beku.")
    parser.add_argument("--captures-root", type=Path, default=Path("results/captures"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("results/captures/dataset_manifest_v1.json"),
    )
    parser.add_argument(
        "--analysis-runs",
        type=Path,
        default=Path("results/analysis_runs.jsonl"),
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        default=Path("results/captures/dataset_analysis_rows_v1.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("results/captures/dataset_analysis_summary_v1.json"),
    )
    parser.add_argument(
        "--visual-evaluation-output",
        type=Path,
        default=Path("results/captures/dataset_visual_evaluation_template_v1.csv"),
    )
    args = parser.parse_args()

    rows, summary = build_summary(args.captures_root, args.manifest, args.analysis_runs)
    args.csv_output.parent.mkdir(parents=True, exist_ok=True)
    with args.csv_output.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    args.summary_output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    visual_fields = [
        "capture_id",
        "ground_truth_cm",
        "repeat_index",
        "image_path",
        "model_id",
        "gemma_description",
        "object_consistency",
        "spatial_consistency",
        "clarity",
        "naturalness",
        "scene_completeness",
        "unsupported_claims",
        "evaluator_notes",
    ]
    with args.visual_evaluation_output.open(
        "w", encoding="utf-8-sig", newline=""
    ) as output_file:
        writer = csv.DictWriter(output_file, fieldnames=visual_fields)
        writer.writeheader()
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        image_paths = {
            entry["capture_id"]: entry["image_path"] for entry in manifest["captures"]
        }
        for row in rows:
            writer.writerow({
                "capture_id": row["capture_id"],
                "ground_truth_cm": row["ground_truth_cm"],
                "repeat_index": row["repeat_index"],
                "image_path": image_paths[row["capture_id"]],
                "model_id": "google/gemma-4-e2b",
                "gemma_description": row["gemma_description"],
                "object_consistency": "",
                "spatial_consistency": "",
                "clarity": "",
                "naturalness": "",
                "scene_completeness": "",
                "unsupported_claims": "",
                "evaluator_notes": "",
            })
    print(json.dumps({
        "dataset_id": summary["dataset_id"],
        "total_captures": summary["total_captures"],
        "csv_output": str(args.csv_output),
        "summary_output": str(args.summary_output),
        "visual_evaluation_output": str(args.visual_evaluation_output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
