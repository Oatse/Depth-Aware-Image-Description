from typing import Final


OBJECT_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "galon air": ("galon air", "galon", "botol air besar", "botol air", "wadah botol air"),
}


def object_matches(annotation: dict[str, str], prediction: dict[str, str]) -> bool:
    expected = annotation.get("main_object", "")
    expected_terms = _object_match_terms(expected)
    return any(_contains(prediction.get("main_object", ""), term) for term in expected_terms)


def position_matches(annotation: dict[str, str], prediction: dict[str, str]) -> bool:
    expected = annotation.get("object_position", "").strip().lower()
    predicted = prediction.get("object_position", "").strip().lower()
    return bool(expected) and predicted == expected


def object_position_joint_matches(annotation: dict[str, str], prediction: dict[str, str]) -> bool:
    return object_matches(annotation, prediction) and position_matches(annotation, prediction)


def obstacle_matches(annotation: dict[str, str], prediction: dict[str, str]) -> bool:
    expected = annotation.get("has_obstacle", "").lower()
    category = prediction.get("distance_category", "")
    if expected == "yes":
        return category in {"sangat_dekat", "dekat"}
    if expected == "no":
        return category in {"sedang", "jauh"}
    return False


def _contains(text: str, needle: str) -> bool:
    return bool(needle) and needle.lower() in text.lower()


def _object_match_terms(expected: str) -> tuple[str, ...]:
    return OBJECT_ALIASES.get(expected.lower().strip(), (expected,))
