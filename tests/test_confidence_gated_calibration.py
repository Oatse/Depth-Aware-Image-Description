from prototypes.confidence_gated_spatial_pilot.calibration import (
    ConfigEvaluation,
    GateConfig,
    PreparedSample,
    candidate_configs,
    evaluate_config,
    paired_risk_difference_interval,
    select_config,
)
from prototypes.confidence_gated_spatial_pilot.gating import SpatialObservation


def _sample(index: int, region: str, category: str, observations: list[tuple[str, str, float]]) -> PreparedSample:
    return PreparedSample(
        sample_index=index,
        ground_truth_nearest_region=region,
        ground_truth_distance_category=category,
        observations=tuple(SpatialObservation(*observation) for observation in observations),
    )


def test_candidate_grid_builds_cartesian_product() -> None:
    configs = candidate_configs(
        {
            "minimum_nearest_region_agreement": [0.6, 0.8],
            "minimum_distance_category_agreement": [0.8, 1.0],
            "maximum_relative_mad": [0.05, 0.12],
        }
    )

    assert len(configs) == 8


def test_select_config_minimizes_risk_then_maximizes_coverage() -> None:
    high_coverage = ConfigEvaluation(GateConfig(0.8, 0.8, 0.12), 0.8, 0.1, 8, 7)
    low_coverage = ConfigEvaluation(GateConfig(1.0, 1.0, 0.05), 0.6, 0.1, 6, 5)
    high_risk = ConfigEvaluation(GateConfig(0.6, 0.6, 0.2), 0.9, 0.2, 9, 7)

    selected = select_config(
        [low_coverage, high_risk, high_coverage],
        minimum_coverage=0.5,
        maximum_coverage=0.9,
    )

    assert selected == high_coverage


def test_evaluate_config_reports_selective_risk() -> None:
    stable_correct = _sample(
        1,
        "lower_center",
        "dekat",
        [("lower_center", "dekat", 1.3)] * 5,
    )
    unstable = _sample(
        2,
        "lower_center",
        "dekat",
        [
            ("lower_left", "dekat", 1.3),
            ("lower_right", "sedang", 1.8),
            ("lower_center", "dekat", 1.4),
            ("lower_left", "sedang", 1.9),
            ("lower_right", "jauh", 2.6),
        ],
    )

    evaluation = evaluate_config(
        [stable_correct, unstable],
        GateConfig(0.8, 0.8, 0.12),
    )

    assert evaluation.coverage == 0.5
    assert evaluation.selective_risk == 0.0


def test_bootstrap_interval_is_reproducible() -> None:
    rows = [
        (True, True, True),
        (False, False, False),
        (True, True, True),
        (False, True, False),
        (True, True, True),
    ]

    first = paired_risk_difference_interval(
        rows,
        resamples=500,
        seed=17,
        confidence_level=0.95,
    )
    second = paired_risk_difference_interval(
        rows,
        resamples=500,
        seed=17,
        confidence_level=0.95,
    )

    assert first == second

