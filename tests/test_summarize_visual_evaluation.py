import csv
import json
from pathlib import Path

from scripts.summarize_visual_evaluation import build_visual_summary


def test_build_visual_summary_preserves_manifest_order_and_separates_scores(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({
        "dataset_id": "dataset-v2",
        "captures": [
            {"capture_id": "cap-1", "ground_truth_cm": 30.0},
            {"capture_id": "cap-2", "ground_truth_cm": 100.0},
        ],
    }), encoding="utf-8")
    scores_path = tmp_path / "scores.csv"
    fields = [
        "capture_id",
        "object_consistency",
        "exact_main_object",
        "spatial_consistency",
        "clarity",
        "naturalness",
        "scene_completeness",
        "unsupported_claims",
        "evaluator_notes",
    ]
    with scores_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows([
            {
                "capture_id": "cap-1",
                "object_consistency": 3,
                "exact_main_object": 0,
                "spatial_consistency": 3,
                "clarity": 4,
                "naturalness": 4,
                "scene_completeness": 3,
                "unsupported_claims": 0,
                "evaluator_notes": "generic",
            },
            {
                "capture_id": "cap-2",
                "object_consistency": 4,
                "exact_main_object": 1,
                "spatial_consistency": 4,
                "clarity": 4,
                "naturalness": 4,
                "scene_completeness": 4,
                "unsupported_claims": 0,
                "evaluator_notes": "exact",
            },
        ])

    summary = build_visual_summary(manifest_path, scores_path)

    assert summary["evaluation_type"] == "single_evaluator_visual_review"
    assert summary["is_uat"] is False
    assert summary["overall"]["exact_main_object_rate"] == 0.5
    assert summary["overall"]["unsupported_claims_total"] == 0
