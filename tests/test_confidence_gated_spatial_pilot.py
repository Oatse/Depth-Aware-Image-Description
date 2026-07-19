import math

from prototypes.confidence_gated_spatial_pilot.gating import (
    SpatialObservation,
    decide_gate,
    relative_mad,
    selective_risk,
)


def _observation(region: str, category: str, score: float) -> SpatialObservation:
    return SpatialObservation(region, category, score)


def test_gate_accepts_stable_claim() -> None:
    observations = [
        _observation("lower_center", "dekat", score)
        for score in (1.30, 1.32, 1.29, 1.31, 1.33)
    ]

    decision = decide_gate(
        observations,
        minimum_nearest_region_agreement=0.8,
        minimum_distance_category_agreement=0.8,
        maximum_relative_mad=0.12,
    )

    assert decision.accepted is True
    assert decision.nearest_region_agreement == 1.0
    assert decision.distance_category_agreement == 1.0
    assert decision.reasons == ()


def test_gate_rejects_region_and_category_disagreement() -> None:
    observations = [
        _observation("lower_center", "dekat", 1.30),
        _observation("lower_left", "sedang", 1.90),
        _observation("lower_right", "dekat", 1.40),
        _observation("lower_center", "sedang", 1.80),
        _observation("lower_left", "jauh", 2.50),
    ]

    decision = decide_gate(
        observations,
        minimum_nearest_region_agreement=0.8,
        minimum_distance_category_agreement=0.8,
        maximum_relative_mad=0.12,
    )

    assert decision.accepted is False
    assert "nearest_region_disagreement" in decision.reasons
    assert "distance_category_disagreement" in decision.reasons


def test_gate_rejects_high_score_dispersion() -> None:
    observations = [
        _observation("lower_center", "dekat", score)
        for score in (1.05, 1.15, 1.30, 1.52, 1.58)
    ]

    decision = decide_gate(
        observations,
        minimum_nearest_region_agreement=0.8,
        minimum_distance_category_agreement=0.8,
        maximum_relative_mad=0.12,
    )

    assert decision.accepted is False
    assert decision.reasons == ("nearest_score_dispersion",)


def test_relative_mad_handles_missing_and_zero_values() -> None:
    assert math.isinf(relative_mad([float("nan"), float("inf")]))
    assert relative_mad([0.0, 0.0]) == 0.0
    assert relative_mad([0.0, 1.0]) == 1.0


def test_selective_risk() -> None:
    assert selective_risk([]) is None
    assert selective_risk([True, True, False, True]) == 0.25
