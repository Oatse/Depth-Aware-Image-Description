import csv
from dataclasses import dataclass
from pathlib import Path


REQUIRED_ANNOTATION_COLUMNS = {
    "image_name",
    "main_object",
    "object_position",
    "distance_category",
    "has_obstacle",
    "safer_direction",
}

DEPTH_EVALUATED_MODES = frozenset({"all", "depth_only", "gemma_depth", "gemma_depth_prompted"})


@dataclass(frozen=True)
class EvaluationSummary:
    total_images: int
    object_accuracy: float
    position_accuracy: float
    distance_category_accuracy: float | None
    obstacle_warning_accuracy: float | None
    description_quality: float
    average_latency_ms: float


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
        summary = EvaluationSummary(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        _write_summary(output_path, {"all": summary})
        return summary

    grouped_predictions = _group_predictions_by_mode(predictions)
    if not grouped_predictions:
        grouped_predictions = {"all": prediction_by_name}

    summaries = {
        mode: _evaluate_matched_rows(mode, [
            (annotation, mode_predictions.get(annotation.get("image_name", ""), {}))
            for annotation in annotations
        ])
        for mode, mode_predictions in grouped_predictions.items()
    }
    _write_summary(output_path, summaries)
    return summaries.get("gemma_depth_prompted") or summaries.get("gemma_depth") or summaries.get("all") or next(iter(summaries.values()))


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
    object_scores = [
        _object_matches(annotation, prediction)
        for annotation, prediction in matched_rows
    ]
    position_scores = [
        _position_matches(annotation, prediction)
        for annotation, prediction in matched_rows
    ]
    distance_scores = [
        prediction.get("distance_category", "") == annotation.get("distance_category", "")
        for annotation, prediction in matched_rows
    ]
    obstacle_scores = [
        _obstacle_matches(annotation, prediction)
        for annotation, prediction in matched_rows
    ]
    quality_scores = [
        _description_quality(annotation, prediction, depth_metrics_apply)
        for annotation, prediction in matched_rows
    ]
    latencies = [
        _to_float(prediction.get("total_latency_ms", "0"))
        for _, prediction in matched_rows
        if prediction
    ]
    return EvaluationSummary(
        total_images=len(matched_rows),
        object_accuracy=_average_bool(object_scores),
        position_accuracy=_average_bool(position_scores),
        distance_category_accuracy=_average_bool(distance_scores) if depth_metrics_apply else None,
        obstacle_warning_accuracy=_average_bool(obstacle_scores) if depth_metrics_apply else None,
        description_quality=sum(quality_scores) / len(quality_scores) if quality_scores else 0.0,
        average_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
    )


def _object_matches(annotation: dict[str, str], prediction: dict[str, str]) -> bool:
    expected = annotation.get("main_object", "")
    return (
        _contains(prediction.get("main_object", ""), expected)
        or _contains(prediction.get("final_description", ""), expected)
        or _contains(prediction.get("description_gemma", ""), expected)
    )


def _position_matches(annotation: dict[str, str], prediction: dict[str, str]) -> bool:
    expected = annotation.get("object_position", "")
    return (
        _contains(prediction.get("object_position", ""), expected)
        or _contains(prediction.get("final_description", ""), expected)
    )


def _contains(text: str, needle: str) -> bool:
    if not needle:
        return False
    return needle.lower() in text.lower()


def _obstacle_matches(annotation: dict[str, str], prediction: dict[str, str]) -> bool:
    expected = annotation.get("has_obstacle", "").lower()
    category = prediction.get("distance_category", "")
    if expected == "yes":
        return category in {"sangat_dekat", "dekat"}
    if expected == "no":
        return category in {"sedang", "jauh"}
    return False


def _description_quality(annotation: dict[str, str], prediction: dict[str, str], depth_metrics_apply: bool) -> float:
    if not prediction:
        return 0.0
    score = 1.0
    max_score = 3.0
    if _object_matches(annotation, prediction):
        score += 1.0
    if _position_matches(annotation, prediction):
        score += 1.0
    if not depth_metrics_apply:
        return min((score / max_score) * 5.0, 5.0)

    max_score += 2.0
    if prediction.get("distance_category") == annotation.get("distance_category", ""):
        score += 1.0
    if _obstacle_matches(annotation, prediction):
        score += 1.0
    return min((score / max_score) * 5.0, 5.0)


def _average_bool(values: list[bool]) -> float:
    return sum(1 for value in values if value) / len(values) if values else 0.0


def _to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _write_summary(output_path: Path, summaries: dict[str, EvaluationSummary]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["mode", *list(EvaluationSummary.__dataclass_fields__.keys())]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for mode, summary in summaries.items():
            row = {
                field: "" if value is None else value
                for field, value in summary.__dict__.items()
            }
            writer.writerow({"mode": mode, **row})
