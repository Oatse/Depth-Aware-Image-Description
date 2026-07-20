def obstacle_confusion(
    matched_rows: list[tuple[dict[str, str], dict[str, str]]],
) -> tuple[int, int, int, int]:
    true_positive = 0
    false_positive = 0
    true_negative = 0
    false_negative = 0
    for annotation, prediction in matched_rows:
        if not prediction or prediction.get("error"):
            continue
        expected = annotation.get("has_obstacle", "").strip().lower()
        category = prediction.get("distance_category", "").strip()
        if expected not in {"yes", "no"} or category not in {"sangat_dekat", "dekat", "sedang", "jauh"}:
            continue
        predicted_positive = category in {"sangat_dekat", "dekat"}
        if expected == "yes" and predicted_positive:
            true_positive += 1
        elif expected == "no" and predicted_positive:
            false_positive += 1
        elif expected == "no":
            true_negative += 1
        else:
            false_negative += 1
    return true_positive, false_positive, true_negative, false_negative


def safe_ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def f1_from_confusion(confusion: tuple[int, int, int, int]) -> float:
    true_positive, false_positive, _, false_negative = confusion
    denominator = (2 * true_positive) + false_positive + false_negative
    return (2 * true_positive) / denominator if denominator else 0.0


def average_bool(values: list[bool]) -> float:
    return sum(1 for value in values if value) / len(values) if values else 0.0


def to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None
