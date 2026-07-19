import csv
from pathlib import Path

from services.evaluation_matching import (
    object_matches,
    object_position_joint_matches,
    obstacle_matches,
    position_matches,
)
from services.evaluation_metrics import (
    average_bool,
    f1_from_confusion,
    obstacle_confusion,
    safe_ratio,
    to_float,
)
from services.evaluation_types import (
    DEPTH_EVALUATED_MODES,
    REQUIRED_ANNOTATION_COLUMNS,
    SEMANTIC_EVALUATED_MODES,
    EvaluationSummary,
)


def evaluate_predictions(
    annotations_path: Path,
    predictions_path: Path,
    output_path: Path,
) -> EvaluationSummary:
    annotations = _read_csv_dicts(annotations_path)
    predictions = _read_csv_dicts(predictions_path)
    _validate_annotations(annotations)

    prediction_by_name = {row.get("image_name", ""): row for row in predictions}
    matched_rows = [
        (annotation, prediction_by_name.get(annotation.get("image_name", ""), {}))
        for annotation in annotations
    ]

    if not matched_rows:
        summary = EvaluationSummary(
            total_images=0,
            prediction_coverage=0.0,
            object_accuracy=0.0,
            position_accuracy=0.0,
            object_position_joint_accuracy=0.0,
            distance_category_accuracy=0.0,
            obstacle_warning_accuracy=0.0,
            obstacle_precision=0.0,
            obstacle_recall=0.0,
            obstacle_f1=0.0,
            obstacle_true_positive=0,
            obstacle_false_positive=0,
            obstacle_true_negative=0,
            obstacle_false_negative=0,
            average_latency_ms=0.0,
        )
        _write_summary(output_path, {("all", "all"): summary})
        return summary

    grouped_predictions = _group_predictions_by_mode(predictions)
    if not grouped_predictions:
        grouped_predictions = {"all": prediction_by_name}

    summaries: dict[tuple[str, str], EvaluationSummary] = {
        (mode, "all"): _evaluate_matched_rows(mode, [
            (annotation, mode_predictions.get(annotation.get("image_name", ""), {}))
            for annotation in annotations
        ])
        for mode, mode_predictions in grouped_predictions.items()
    }
    source_subsets = sorted({
        annotation.get("source_subset", "").strip()
        for annotation in annotations
        if annotation.get("source_subset", "").strip()
    })
    for mode, mode_predictions in grouped_predictions.items():
        for source_subset in source_subsets:
            subset_rows = [
                (annotation, mode_predictions.get(annotation.get("image_name", ""), {}))
                for annotation in annotations
                if annotation.get("source_subset", "").strip() == source_subset
            ]
            summaries[(mode, f"source_subset:{source_subset}")] = _evaluate_matched_rows(mode, subset_rows)
    _write_summary(output_path, summaries)
    complete_summaries = {
        mode: summary
        for (mode, scope), summary in summaries.items()
        if scope == "all" and summary.prediction_coverage == 1.0
    }
    return (
        complete_summaries.get("gemma_depth")
        or complete_summaries.get("all")
        or next(iter(complete_summaries.values()), next(iter(summaries.values())))
    )


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _validate_annotations(rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    missing = REQUIRED_ANNOTATION_COLUMNS - set(rows[0].keys())
    if missing:
        raise ValueError(f"Missing annotation columns: {', '.join(sorted(missing))}")


def _group_predictions_by_mode(rows: list[dict[str, str]]) -> dict[str, dict[str, dict[str, str]]]:
    grouped: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        mode = row.get("mode", "all") or "all"
        image_name = row.get("image_name", "")
        if not image_name:
            continue
        grouped.setdefault(mode, {})[image_name] = row
    return grouped


def _evaluate_matched_rows(mode: str, matched_rows: list[tuple[dict[str, str], dict[str, str]]]) -> EvaluationSummary:
    depth_metrics_apply = mode in DEPTH_EVALUATED_MODES
    semantic_metrics_apply = mode in SEMANTIC_EVALUATED_MODES
    completed_predictions = [
        prediction
        for _, prediction in matched_rows
        if prediction and not prediction.get("error")
    ]
    object_scores = [
        object_matches(annotation, prediction)
        for annotation, prediction in matched_rows
    ]
    position_scores = [
        position_matches(annotation, prediction)
        for annotation, prediction in matched_rows
    ]
    distance_scores = [
        prediction.get("distance_category", "") == annotation.get("distance_category", "")
        for annotation, prediction in matched_rows
    ]
    joint_scores = [
        object_position_joint_matches(annotation, prediction)
        for annotation, prediction in matched_rows
    ]
    obstacle_scores = [
        obstacle_matches(annotation, prediction)
        for annotation, prediction in matched_rows
    ]
    confusion = obstacle_confusion(matched_rows) if depth_metrics_apply else None
    latencies = [
        to_float(prediction.get("total_latency_ms", "0"))
        for _, prediction in matched_rows
        if prediction
    ]
    return EvaluationSummary(
        total_images=len(matched_rows),
        prediction_coverage=len(completed_predictions) / len(matched_rows) if matched_rows else 0.0,
        object_accuracy=average_bool(object_scores) if semantic_metrics_apply else None,
        position_accuracy=average_bool(position_scores) if semantic_metrics_apply else None,
        object_position_joint_accuracy=average_bool(joint_scores) if semantic_metrics_apply else None,
        distance_category_accuracy=average_bool(distance_scores) if depth_metrics_apply else None,
        obstacle_warning_accuracy=average_bool(obstacle_scores) if depth_metrics_apply else None,
        obstacle_precision=safe_ratio(confusion[0], confusion[0] + confusion[1]) if confusion else None,
        obstacle_recall=safe_ratio(confusion[0], confusion[0] + confusion[3]) if confusion else None,
        obstacle_f1=f1_from_confusion(confusion) if confusion else None,
        obstacle_true_positive=confusion[0] if confusion else None,
        obstacle_false_positive=confusion[1] if confusion else None,
        obstacle_true_negative=confusion[2] if confusion else None,
        obstacle_false_negative=confusion[3] if confusion else None,
        average_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
    )


def _write_summary(
    output_path: Path,
    summaries: dict[tuple[str, str], EvaluationSummary],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["mode", "evaluation_scope", *list(EvaluationSummary.__dataclass_fields__.keys())]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for (mode, evaluation_scope), summary in summaries.items():
            row = {
                field: "" if getattr(summary, field) is None else getattr(summary, field)
                for field in EvaluationSummary.__dataclass_fields__
            }
            writer.writerow({"mode": mode, "evaluation_scope": evaluation_scope, **row})
