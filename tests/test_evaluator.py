import csv
from pathlib import Path

from services.evaluator import evaluate_predictions


def test_evaluator_computes_basic_metrics(tmp_path: Path) -> None:
    annotations = tmp_path / "annotations.csv"
    predictions = tmp_path / "predictions.csv"
    output = tmp_path / "evaluation.csv"

    with annotations.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image_name",
                "main_object",
                "object_position",
                "distance_meter",
                "distance_category",
                "has_obstacle",
                "front_area_status",
                "safer_direction",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "image_name": "img_001.jpg",
            "main_object": "kursi",
            "object_position": "tengah",
            "distance_meter": "0.8",
            "distance_category": "dekat",
            "has_obstacle": "yes",
            "front_area_status": "terhalang",
            "safer_direction": "kanan",
            "notes": "",
        })

    with predictions.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image_name",
                "final_description",
                "distance_category",
                "total_latency_ms",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "image_name": "img_001.jpg",
            "final_description": "Terlihat kursi di area tengah.",
            "distance_category": "dekat",
            "total_latency_ms": "120",
        })

    summary = evaluate_predictions(annotations, predictions, output)

    assert summary.total_images == 1
    assert summary.object_accuracy == 1.0
    assert summary.position_accuracy == 1.0
    assert summary.distance_category_accuracy == 1.0
    assert output.exists()


def test_evaluator_marks_depth_metrics_not_applicable_for_gemma_baseline(tmp_path: Path) -> None:
    annotations = tmp_path / "annotations.csv"
    predictions = tmp_path / "predictions.csv"
    output = tmp_path / "evaluation.csv"

    with annotations.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image_name",
                "main_object",
                "object_position",
                "distance_category",
                "has_obstacle",
                "safer_direction",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "image_name": "img_001.jpg",
            "main_object": "kursi",
            "object_position": "tengah",
            "distance_category": "dekat",
            "has_obstacle": "yes",
            "safer_direction": "kanan",
        })

    with predictions.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image_name",
                "mode",
                "final_description",
                "distance_category",
                "total_latency_ms",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "image_name": "img_001.jpg",
            "mode": "gemma_only",
            "final_description": "Terlihat kursi di area tengah.",
            "distance_category": "",
            "total_latency_ms": "120",
        })

    summary = evaluate_predictions(annotations, predictions, output)

    assert summary.object_accuracy == 1.0
    assert summary.position_accuracy == 1.0
    assert summary.distance_category_accuracy is None
    assert summary.obstacle_warning_accuracy is None
    assert summary.description_quality == 5.0
    rows = list(csv.DictReader(output.open(newline="", encoding="utf-8")))
    assert rows[0]["distance_category_accuracy"] == ""
