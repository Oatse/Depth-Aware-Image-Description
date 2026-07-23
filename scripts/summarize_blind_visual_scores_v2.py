import argparse
import csv
import hashlib
import json
import random
from pathlib import Path
from statistics import fmean
from typing import Any


SCORE_FIELDS = (
    "object_consistency",
    "spatial_consistency",
    "clarity",
    "naturalness",
    "scene_completeness",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _bootstrap_ci(values: list[float], *, seed: int, iterations: int) -> list[float]:
    rng = random.Random(seed)
    samples = [
        fmean(rng.choice(values) for _ in values)
        for _ in range(iterations)
    ]
    return [
        round(_percentile(samples, 0.025), 4),
        round(_percentile(samples, 0.975), 4),
    ]


def summarize(
    scores_path: Path,
    key_path: Path,
    lock_path: Path,
    *,
    bootstrap_iterations: int = 10_000,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if _sha256(scores_path) != lock.get("scored_template_sha256"):
        raise ValueError("Checksum skor tidak sama dengan score lock.")
    scores = _read_csv(scores_path)
    keys = _read_csv(key_path)
    score_by_id = {row["evaluation_item_id"]: row for row in scores}
    key_by_id = {row["evaluation_item_id"]: row for row in keys}
    if len(score_by_id) != 36 or set(score_by_id) != set(key_by_id):
        raise ValueError("Item skor dan key tidak membentuk 36 pasangan yang sama.")

    merged: list[dict[str, Any]] = []
    for item_id, score in score_by_id.items():
        if score.get("manual_review_status") != "completed":
            raise ValueError(f"Skor belum selesai: {item_id}")
        key = key_by_id[item_id]
        merged.append(
            {
                "evaluation_item_id": item_id,
                "capture_id": key["capture_id"],
                "mode": key["mode"],
                "source_image_sha256": key["source_image_sha256"],
                **{field: float(score[field]) for field in SCORE_FIELDS},
                "unsupported_claims": int(score["unsupported_claims"]),
            }
        )

    by_capture: dict[str, dict[str, dict[str, Any]]] = {}
    for row in merged:
        by_capture.setdefault(row["capture_id"], {})[row["mode"]] = row
    if len(by_capture) != 18:
        raise ValueError("Jumlah capture hasil unblind bukan 18.")

    paired_rows: list[dict[str, Any]] = []
    for capture_id, modes in sorted(by_capture.items()):
        if set(modes) != {"gemma_only", "sensor_assisted"}:
            raise ValueError(f"Mode tidak lengkap: {capture_id}")
        baseline = modes["gemma_only"]
        assisted = modes["sensor_assisted"]
        if baseline["source_image_sha256"] != assisted["source_image_sha256"]:
            raise ValueError(f"Checksum gambar pasangan berbeda: {capture_id}")
        row: dict[str, Any] = {
            "capture_id": capture_id,
            "source_image_sha256": baseline["source_image_sha256"],
        }
        for field in SCORE_FIELDS:
            row[f"gemma_only_{field}"] = baseline[field]
            row[f"sensor_assisted_{field}"] = assisted[field]
            row[f"delta_{field}"] = round(assisted[field] - baseline[field], 4)
        baseline_overall = fmean(baseline[field] for field in SCORE_FIELDS)
        assisted_overall = fmean(assisted[field] for field in SCORE_FIELDS)
        row["gemma_only_overall_mean"] = round(baseline_overall, 4)
        row["sensor_assisted_overall_mean"] = round(assisted_overall, 4)
        row["delta_overall_mean"] = round(assisted_overall - baseline_overall, 4)
        row["gemma_only_unsupported_claims"] = baseline["unsupported_claims"]
        row["sensor_assisted_unsupported_claims"] = assisted["unsupported_claims"]
        paired_rows.append(row)

    mode_summary: dict[str, Any] = {}
    for mode in ("gemma_only", "sensor_assisted"):
        mode_rows = [row for row in merged if row["mode"] == mode]
        mode_summary[mode] = {
            "n_images": len(mode_rows),
            **{
                f"mean_{field}": round(fmean(row[field] for row in mode_rows), 4)
                for field in SCORE_FIELDS
            },
            "mean_overall": round(
                fmean(
                    fmean(row[field] for field in SCORE_FIELDS)
                    for row in mode_rows
                ),
                4,
            ),
            "unsupported_claims_total": sum(row["unsupported_claims"] for row in mode_rows),
        }

    paired_deltas = {
        field: [float(row[f"delta_{field}"]) for row in paired_rows]
        for field in (*SCORE_FIELDS, "overall_mean")
    }
    comparison = {
        field: {
            "mean_delta_sensor_assisted_minus_gemma_only": round(fmean(values), 4),
            "bootstrap_95_ci": _bootstrap_ci(
                values,
                seed=20260723 + index,
                iterations=bootstrap_iterations,
            ),
        }
        for index, (field, values) in enumerate(paired_deltas.items())
    }
    overall_values = paired_deltas["overall_mean"]
    summary = {
        "schema_version": 1,
        "evaluation_design": "paired_blind_single_evaluator",
        "independent_images": 18,
        "scored_items": 36,
        "items_per_image": 2,
        "score_lock_sha256": _sha256(lock_path),
        "scored_template_sha256": _sha256(scores_path),
        "mode_summary": mode_summary,
        "paired_comparison": comparison,
        "overall_pair_outcomes": {
            "sensor_assisted_higher": sum(value > 0 for value in overall_values),
            "tie": sum(value == 0 for value in overall_values),
            "gemma_only_higher": sum(value < 0 for value in overall_values),
        },
        "bootstrap": {
            "unit": "capture_pair",
            "iterations": bootstrap_iterations,
            "seed_base": 20260723,
        },
        "limitations": lock["limitations"]
        + [
            "Interval bootstrap mengukur ketidakpastian pada 18 pasangan dalam satu setup, bukan generalisasi populasi.",
            "Dataset hanya memuat satu objek utama dan satu lingkungan indoor terkendali.",
        ],
    }
    return summary, paired_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Unblind skor terkunci dan ringkas per mode.")
    parser.add_argument(
        "--scores",
        type=Path,
        default=Path("results/captures/dataset_visual_evaluation_v2_fresh.csv"),
    )
    parser.add_argument(
        "--key",
        type=Path,
        default=Path("results/captures/dataset_visual_evaluation_key_v2_fresh.csv"),
    )
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path("results/captures/dataset_visual_evaluation_score_lock_v2_fresh.json"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("results/captures/dataset_visual_summary_v2_fresh.json"),
    )
    parser.add_argument(
        "--paired-output",
        type=Path,
        default=Path("results/captures/dataset_visual_paired_comparison_v2_fresh.csv"),
    )
    args = parser.parse_args()
    summary, paired_rows = summarize(args.scores, args.key, args.lock)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with args.paired_output.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=paired_rows[0].keys())
        writer.writeheader()
        writer.writerows(paired_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
