from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class SpatialObservation:
    nearest_region: str
    distance_category: str
    nearest_score: float


@dataclass(frozen=True)
class GateDecision:
    accepted: bool
    nearest_region: str
    distance_category: str
    nearest_region_agreement: float
    distance_category_agreement: float
    relative_mad: float
    reasons: tuple[str, ...]


def modal_value(values: Iterable[str]) -> tuple[str, float]:
    values_list = list(values)
    if not values_list:
        raise ValueError("At least one value is required.")
    counts = Counter(values_list)
    first_position = {value: values_list.index(value) for value in counts}
    mode, count = min(
        counts.items(),
        key=lambda item: (-item[1], first_position[item[0]]),
    )
    return mode, count / len(values_list)


def relative_mad(values: Iterable[float]) -> float:
    array = np.asarray(list(values), dtype=np.float64)
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return float("inf")
    median = float(np.median(finite))
    if abs(median) <= 1e-12:
        return 0.0 if np.allclose(finite, 0.0) else float("inf")
    mad = float(np.median(np.abs(finite - median)))
    return mad / abs(median)


def decide_gate(
    observations: Iterable[SpatialObservation],
    *,
    minimum_nearest_region_agreement: float,
    minimum_distance_category_agreement: float,
    maximum_relative_mad: float,
) -> GateDecision:
    observations_list = list(observations)
    if not observations_list:
        raise ValueError("At least one observation is required.")

    region, region_agreement = modal_value(item.nearest_region for item in observations_list)
    category, category_agreement = modal_value(item.distance_category for item in observations_list)
    scores = [
        item.nearest_score
        for item in observations_list
        if item.nearest_region == region
    ]
    dispersion = relative_mad(scores)

    reasons: list[str] = []
    if region_agreement < minimum_nearest_region_agreement:
        reasons.append("nearest_region_disagreement")
    if category_agreement < minimum_distance_category_agreement:
        reasons.append("distance_category_disagreement")
    if dispersion > maximum_relative_mad:
        reasons.append("nearest_score_dispersion")

    return GateDecision(
        accepted=not reasons,
        nearest_region=region,
        distance_category=category,
        nearest_region_agreement=region_agreement,
        distance_category_agreement=category_agreement,
        relative_mad=dispersion,
        reasons=tuple(reasons),
    )


def selective_risk(correctness: Iterable[bool]) -> float | None:
    values = list(correctness)
    if not values:
        return None
    return 1.0 - (sum(values) / len(values))

