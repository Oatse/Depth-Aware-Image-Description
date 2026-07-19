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
                "distance_annotation_basis",
                "annotation_confidence",
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
            "distance_annotation_basis": "visual_relative",
            "annotation_confidence": "medium",
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
                "main_object",
                "object_position",
                "final_description",
                "distance_category",
                "total_latency_ms",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "image_name": "img_001.jpg",
            "main_object": "kursi",
            "object_position": "tengah",
            "final_description": "Terlihat kursi di area tengah.",
            "distance_category": "dekat",
            "total_latency_ms": "120",
        })

    summary = evaluate_predictions(annotations, predictions, output)

    assert summary.total_images == 1
    assert summary.prediction_coverage == 1.0
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
                "main_object",
                "object_position",
                "final_description",
                "distance_category",
                "total_latency_ms",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "image_name": "img_001.jpg",
            "mode": "gemma_only",
            "main_object": "kursi",
            "object_position": "tengah",
            "final_description": "Terlihat kursi di area tengah.",
            "distance_category": "",
            "total_latency_ms": "120",
        })

    summary = evaluate_predictions(annotations, predictions, output)

    assert summary.object_accuracy == 1.0
    assert summary.position_accuracy == 1.0
    assert summary.distance_category_accuracy is None
    assert summary.obstacle_warning_accuracy is None
    assert summary.object_position_joint_accuracy == 1.0
    rows = list(csv.DictReader(output.open(newline="", encoding="utf-8")))
    assert rows[0]["distance_category_accuracy"] == ""


def test_evaluator_matches_limited_object_synonyms(tmp_path: Path) -> None:
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
            "main_object": "galon air",
            "object_position": "kiri",
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
                "main_object",
                "object_position",
                "final_description",
                "distance_category",
                "total_latency_ms",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "image_name": "img_001.jpg",
            "mode": "gemma_depth",
            "main_object": "botol air besar",
            "object_position": "kiri",
            "final_description": "Terlihat beberapa botol air besar di lantai kiri.",
            "distance_category": "dekat",
            "total_latency_ms": "120",
        })

    summary = evaluate_predictions(annotations, predictions, output)

    assert summary.object_accuracy == 1.0


def test_evaluator_returns_complete_depth_mode_when_another_mode_is_incomplete(tmp_path: Path) -> None:
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
        writer.writerows([
            {
                "image_name": "img_001.jpg",
                "main_object": "kursi",
                "object_position": "tengah",
                "distance_category": "dekat",
                "has_obstacle": "yes",
                "safer_direction": "kanan",
            },
            {
                "image_name": "img_002.jpg",
                "main_object": "pintu",
                "object_position": "tengah",
                "distance_category": "jauh",
                "has_obstacle": "no",
                "safer_direction": "tengah",
            },
        ])

    with predictions.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image_name",
                "mode",
                "main_object",
                "object_position",
                "final_description",
                "distance_category",
                "total_latency_ms",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows([
            {
                "image_name": "img_001.jpg",
                "mode": "gemma_only",
                "main_object": "",
                "object_position": "",
                "final_description": "",
                "distance_category": "",
                "total_latency_ms": "240000",
                "error": "Gemma inference failed.",
            },
            {
                "image_name": "img_001.jpg",
                "mode": "gemma_depth",
                "main_object": "kursi",
                "object_position": "tengah",
                "final_description": "Terlihat kursi di area tengah.",
                "distance_category": "dekat",
                "total_latency_ms": "100",
                "error": "",
            },
            {
                "image_name": "img_002.jpg",
                "mode": "gemma_depth",
                "main_object": "pintu",
                "object_position": "tengah",
                "final_description": "Terlihat pintu di area tengah.",
                "distance_category": "jauh",
                "total_latency_ms": "100",
                "error": "",
            },
        ])

    summary = evaluate_predictions(annotations, predictions, output)

    assert summary.prediction_coverage == 1.0
    assert summary.distance_category_accuracy == 1.0
    rows = list(csv.DictReader(output.open(newline="", encoding="utf-8")))
    coverage_by_mode = {row["mode"]: row["prediction_coverage"] for row in rows}
    assert coverage_by_mode["gemma_depth"] == "1.0"
    assert coverage_by_mode["gemma_only"] == "0.0"


def test_evaluator_reports_obstacle_confusion_matrix_and_f1(tmp_path: Path) -> None:
    annotations = tmp_path / "annotations.csv"
    predictions = tmp_path / "predictions.csv"
    output = tmp_path / "evaluation.csv"
    fieldnames = [
        "image_name",
        "main_object",
        "object_position",
        "distance_category",
        "has_obstacle",
        "safer_direction",
    ]
    with annotations.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, has_obstacle in enumerate(("yes", "yes", "no", "no"), start=1):
            writer.writerow({
                "image_name": f"img_{index:03d}.jpg",
                "main_object": "kursi",
                "object_position": "tengah",
                "distance_category": "dekat" if has_obstacle == "yes" else "jauh",
                "has_obstacle": has_obstacle,
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
        for index, category in enumerate(("dekat", "jauh", "dekat", "jauh"), start=1):
            writer.writerow({
                "image_name": f"img_{index:03d}.jpg",
                "mode": "gemma_depth",
                "final_description": "Terlihat kursi di tengah.",
                "distance_category": category,
                "total_latency_ms": "10",
            })

    summary = evaluate_predictions(annotations, predictions, output)

    assert summary.obstacle_true_positive == 1
    assert summary.obstacle_false_positive == 1
    assert summary.obstacle_true_negative == 1
    assert summary.obstacle_false_negative == 1
    assert summary.obstacle_precision == 0.5
    assert summary.obstacle_recall == 0.5
    assert summary.obstacle_f1 == 0.5


def test_evaluator_does_not_expose_rouge_without_a_caption_benchmark(tmp_path: Path) -> None:
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
                "reference_description",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows([
            {
                "image_name": "img_001.jpg",
                "main_object": "kursi",
                "object_position": "tengah",
                "distance_category": "dekat",
                "has_obstacle": "yes",
                "safer_direction": "kanan",
                "reference_description": "Kursi berada dekat di tengah.",
                "notes": "Catatan ini bukan referensi.",
            },
            {
                "image_name": "img_002.jpg",
                "main_object": "pintu",
                "object_position": "kanan",
                "distance_category": "jauh",
                "has_obstacle": "no",
                "safer_direction": "tengah",
                "reference_description": "",
                "notes": "Pintu jauh di kanan.",
            },
        ])
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
        writer.writerows([
            {
                "image_name": "img_001.jpg",
                "mode": "gemma_depth",
                "final_description": "Kursi berada dekat di tengah.",
                "distance_category": "dekat",
                "total_latency_ms": "10",
            },
            {
                "image_name": "img_002.jpg",
                "mode": "gemma_depth",
                "final_description": "Pintu jauh di kanan.",
                "distance_category": "jauh",
                "total_latency_ms": "10",
            },
        ])

    summary = evaluate_predictions(annotations, predictions, output)

    with output.open(newline="", encoding="utf-8") as handle:
        fieldnames = csv.DictReader(handle).fieldnames or []

    assert not hasattr(summary, "rouge_l_f1")
    assert "rouge_l_f1" not in fieldnames
    assert "rouge_l_reference_coverage" not in fieldnames


def test_evaluator_does_not_credit_position_words_from_free_text(tmp_path: Path) -> None:
    # Given
    annotations, predictions, output = _write_single_evaluation_case(
        tmp_path,
        annotation_position="kiri",
        prediction_position="kanan",
        final_description="Terlihat meja; region kiri merupakan area depth terdekat.",
    )

    # When
    summary = evaluate_predictions(annotations, predictions, output)

    # Then
    assert summary.position_accuracy == 0.0


def test_evaluator_reports_joint_object_position_accuracy(tmp_path: Path) -> None:
    # Given
    annotations, predictions, output = _write_single_evaluation_case(
        tmp_path,
        annotation_position="kiri",
        prediction_position="kanan",
        final_description="Terlihat kursi di kiri.",
    )

    # When
    summary = evaluate_predictions(annotations, predictions, output)

    # Then
    assert summary.object_accuracy == 1.0
    assert summary.position_accuracy == 0.0
    assert summary.object_position_joint_accuracy == 0.0


def test_evaluator_marks_semantic_metrics_not_applicable_for_depth_only(tmp_path: Path) -> None:
    # Given
    annotations, predictions, output = _write_single_evaluation_case(
        tmp_path,
        annotation_position="kiri",
        prediction_position="",
        final_description="Region kiri merupakan area depth terdekat.",
        mode="depth_only",
        prediction_object="",
    )

    # When
    summary = evaluate_predictions(annotations, predictions, output)

    # Then
    assert summary.object_accuracy is None
    assert summary.position_accuracy is None
    assert summary.object_position_joint_accuracy is None


def test_evaluator_removes_handcrafted_description_quality_score(tmp_path: Path) -> None:
    # Given
    annotations, predictions, output = _write_single_evaluation_case(tmp_path)

    # When
    summary = evaluate_predictions(annotations, predictions, output)
    with output.open(newline="", encoding="utf-8") as handle:
        fieldnames = csv.DictReader(handle).fieldnames or []

    # Then
    assert not hasattr(summary, "description_quality")
    assert "description_quality" not in fieldnames


def test_evaluator_reports_temporal_holdout_subsets_separately(tmp_path: Path) -> None:
    # Given
    annotations, predictions, output = _write_two_subset_evaluation_cases(tmp_path)

    # When
    evaluate_predictions(annotations, predictions, output)
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    # Then
    scopes = {row["evaluation_scope"] for row in rows}
    assert scopes == {
        "all",
        "source_subset:original_30",
        "source_subset:sample_new_balancing_medium_far",
    }


def _write_single_evaluation_case(
    tmp_path: Path,
    annotation_position: str = "kiri",
    prediction_position: str = "kiri",
    final_description: str = "Terlihat kursi di kiri.",
    mode: str = "gemma_depth",
    prediction_object: str = "kursi",
) -> tuple[Path, Path, Path]:
    annotations = tmp_path / "annotations.csv"
    predictions = tmp_path / "predictions.csv"
    output = tmp_path / "evaluation.csv"
    with annotations.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image_name",
                "source_subset",
                "main_object",
                "object_position",
                "distance_annotation_basis",
                "annotation_confidence",
                "distance_category",
                "has_obstacle",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "image_name": "img_001.jpg",
            "source_subset": "original_30",
            "main_object": "kursi",
            "object_position": annotation_position,
            "distance_annotation_basis": "visual_relative",
            "annotation_confidence": "medium",
            "distance_category": "dekat",
            "has_obstacle": "yes",
        })
    with predictions.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image_name",
                "mode",
                "main_object",
                "object_position",
                "final_description",
                "distance_category",
                "total_latency_ms",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "image_name": "img_001.jpg",
            "mode": mode,
            "main_object": prediction_object,
            "object_position": prediction_position,
            "final_description": final_description,
            "distance_category": "dekat",
            "total_latency_ms": "10",
            "error": "",
        })
    return annotations, predictions, output


def _write_two_subset_evaluation_cases(tmp_path: Path) -> tuple[Path, Path, Path]:
    annotations = tmp_path / "annotations.csv"
    predictions = tmp_path / "predictions.csv"
    output = tmp_path / "evaluation.csv"
    with annotations.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image_name",
                "source_subset",
                "main_object",
                "object_position",
                "distance_annotation_basis",
                "annotation_confidence",
                "distance_category",
                "has_obstacle",
            ],
        )
        writer.writeheader()
        writer.writerows([
            {
                "image_name": "img_001.jpg",
                "source_subset": "original_30",
                "main_object": "kursi",
                "object_position": "kiri",
                "distance_annotation_basis": "visual_relative",
                "annotation_confidence": "medium",
                "distance_category": "dekat",
                "has_obstacle": "yes",
            },
            {
                "image_name": "img_002.jpg",
                "source_subset": "sample_new_balancing_medium_far",
                "main_object": "pintu",
                "object_position": "kanan",
                "distance_annotation_basis": "visual_relative",
                "annotation_confidence": "medium",
                "distance_category": "jauh",
                "has_obstacle": "no",
            },
        ])
    with predictions.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image_name",
                "mode",
                "main_object",
                "object_position",
                "final_description",
                "distance_category",
                "total_latency_ms",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows([
            {
                "image_name": "img_001.jpg",
                "mode": "gemma_depth",
                "main_object": "kursi",
                "object_position": "kiri",
                "final_description": "Terlihat kursi di kiri.",
                "distance_category": "dekat",
                "total_latency_ms": "10",
                "error": "",
            },
            {
                "image_name": "img_002.jpg",
                "mode": "gemma_depth",
                "main_object": "pintu",
                "object_position": "kanan",
                "final_description": "Terlihat pintu di kanan.",
                "distance_category": "jauh",
                "total_latency_ms": "10",
                "error": "",
            },
        ])
    return annotations, predictions, output
