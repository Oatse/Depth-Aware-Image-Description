import argparse
import csv
import json
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


def build_visual_summary(
    manifest_path: Path,
    scores_path: Path,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_rows = manifest["captures"]
    expected_ids = [str(row["capture_id"]) for row in manifest_rows]
    distance_by_id = {
        str(row["capture_id"]): float(row["ground_truth_cm"])
        for row in manifest_rows
    }
    with scores_path.open(encoding="utf-8", newline="") as input_file:
        rows = list(csv.DictReader(input_file))
    actual_ids = [str(row["capture_id"]) for row in rows]
    if actual_ids != expected_ids:
        raise ValueError("Urutan atau capture_id skor visual tidak sama dengan manifest.")

    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized_row = dict(row)
        for field in SCORE_FIELDS:
            score = int(row[field])
            if score not in {1, 2, 3, 4}:
                raise ValueError(f"Skor {field} di luar rentang 1-4: {row['capture_id']}")
            normalized_row[field] = score
        normalized_row["exact_main_object"] = int(row["exact_main_object"])
        normalized_row["unsupported_claims"] = int(row["unsupported_claims"])
        normalized_row["ground_truth_cm"] = distance_by_id[str(row["capture_id"])]
        normalized.append(normalized_row)

    by_distance = []
    for distance in sorted(set(distance_by_id.values())):
        group = [row for row in normalized if row["ground_truth_cm"] == distance]
        by_distance.append({
            "ground_truth_cm": distance,
            "n": len(group),
            "exact_main_object_rate": round(fmean(row["exact_main_object"] for row in group), 4),
            **{
                f"{field}_mean": round(fmean(row[field] for row in group), 4)
                for field in SCORE_FIELDS
            },
            "unsupported_claims_total": sum(row["unsupported_claims"] for row in group),
        })

    return {
        "schema_version": 1,
        "dataset_id": manifest["dataset_id"],
        "evaluation_type": "single_evaluator_visual_review",
        "is_uat": False,
        "score_scale": {
            "4": "tepat, jelas, dan mencakup unsur utama yang terlihat",
            "3": "didukung gambar tetapi generik atau memiliki kekurangan kecil",
            "2": "sebagian didukung namun ambigu atau memiliki kesalahan penting",
            "1": "tidak didukung atau tidak memadai",
        },
        "total_captures": len(normalized),
        "overall": {
            "exact_main_object_count": sum(row["exact_main_object"] for row in normalized),
            "exact_main_object_rate": round(fmean(row["exact_main_object"] for row in normalized), 4),
            **{
                f"{field}_mean": round(fmean(row[field] for row in normalized), 4)
                for field in SCORE_FIELDS
            },
            "unsupported_claims_total": sum(row["unsupported_claims"] for row in normalized),
            "captures_with_unsupported_claims": sum(
                row["unsupported_claims"] > 0 for row in normalized
            ),
        },
        "by_distance": by_distance,
        "limitations": [
            "Penilaian dilakukan oleh satu evaluator teknis dan bukan UAT.",
            "Skor tidak membuktikan manfaat pengguna atau keselamatan navigasi.",
            "Dataset memakai satu target koper dan satu setup indoor terkendali.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Rekap skor evaluasi visual dataset capture.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("results/captures/dataset_manifest_v2.json"),
    )
    parser.add_argument(
        "--scores",
        type=Path,
        default=Path("results/captures/dataset_visual_scores_v2.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/captures/dataset_visual_summary_v2.json"),
    )
    args = parser.parse_args()
    summary = build_visual_summary(args.manifest, args.scores)
    args.output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
