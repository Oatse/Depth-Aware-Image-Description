from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

import numpy as np

from prototypes.confidence_gated_spatial_pilot.gating import (
    GateDecision,
    SpatialObservation,
    decide_gate,
    selective_risk,
)


@dataclass(frozen=True)
class GateConfig:
    minimum_nearest_region_agreement: float
    minimum_distance_category_agreement: float
    maximum_relative_mad: float


@dataclass(frozen=True)
class PreparedSample:
    sample_index: int
    ground_truth_nearest_region: str
    ground_truth_distance_category: str
    observations: tuple[SpatialObservation, ...]


@dataclass(frozen=True)
class ConfigEvaluation:
    config: GateConfig
    coverage: float
    selective_risk: float | None
    accepted_count: int
    correct_accepted_count: int


def candidate_configs(grid: dict[str, list[float]]) -> list[GateConfig]:
    return [
        GateConfig(region, category, dispersion)
        for region, category, dispersion in product(
            grid["minimum_nearest_region_agreement"],
            grid["minimum_distance_category_agreement"],
            grid["maximum_relative_mad"],
        )
    ]


def decision_for_sample(sample: PreparedSample, config: GateConfig) -> GateDecision:
    return decide_gate(
        sample.observations,
        minimum_nearest_region_agreement=config.minimum_nearest_region_agreement,
        minimum_distance_category_agreement=config.minimum_distance_category_agreement,
        maximum_relative_mad=config.maximum_relative_mad,
    )


def joint_correct(
    nearest_region: str,
    distance_category: str,
    sample: PreparedSample,
) -> bool:
    return (
        nearest_region == sample.ground_truth_nearest_region
        and distance_category == sample.ground_truth_distance_category
    )


def evaluate_config(
    samples: Iterable[PreparedSample],
    config: GateConfig,
) -> ConfigEvaluation:
    materialized = list(samples)
    correctness: list[bool] = []
    for sample in materialized:
        decision = decision_for_sample(sample, config)
        if decision.accepted:
            correctness.append(
                joint_correct(
                    decision.nearest_region,
                    decision.distance_category,
                    sample,
                )
            )
    accepted_count = len(correctness)
    return ConfigEvaluation(
        config=config,
        coverage=accepted_count / len(materialized) if materialized else 0.0,
        selective_risk=selective_risk(correctness),
        accepted_count=accepted_count,
        correct_accepted_count=sum(correctness),
    )


def select_config(
    evaluations: Iterable[ConfigEvaluation],
    *,
    minimum_coverage: float,
    maximum_coverage: float,
) -> ConfigEvaluation:
    feasible = [
        evaluation
        for evaluation in evaluations
        if evaluation.selective_risk is not None
        and minimum_coverage <= evaluation.coverage <= maximum_coverage
    ]
    if not feasible:
        raise ValueError("No gate configuration satisfies the calibration coverage constraint.")
    return min(
        feasible,
        key=lambda evaluation: (
            evaluation.selective_risk,
            -evaluation.coverage,
            -evaluation.config.minimum_nearest_region_agreement,
            -evaluation.config.minimum_distance_category_agreement,
            evaluation.config.maximum_relative_mad,
        ),
    )


def paired_risk_difference_interval(
    rows: Iterable[tuple[bool, bool, bool]],
    *,
    resamples: int,
    seed: int,
    confidence_level: float,
) -> tuple[float, float] | None:
    materialized = list(rows)
    if not materialized:
        return None
    generator = np.random.default_rng(seed)
    differences: list[float] = []
    sample_count = len(materialized)
    for _ in range(resamples):
        indices = generator.integers(0, sample_count, size=sample_count)
        sampled = [materialized[index] for index in indices]
        always = [always_correct for always_correct, _, _ in sampled]
        gated = [
            gated_correct
            for _, accepted, gated_correct in sampled
            if accepted
        ]
        always_risk = selective_risk(always)
        gated_risk = selective_risk(gated)
        if always_risk is not None and gated_risk is not None:
            differences.append(gated_risk - always_risk)
    if not differences:
        return None
    alpha = 1.0 - confidence_level
    low, high = np.quantile(differences, [alpha / 2.0, 1.0 - alpha / 2.0])
    return float(low), float(high)

