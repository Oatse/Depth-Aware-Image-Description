from __future__ import annotations

import re
from dataclasses import dataclass
from typing import assert_never

from prototypes.depth_guided_roi_v3.models import CLASS_TERMS, ExperimentCondition


REQUIRED_STRUCTURED_OUTPUT_COMPLIANCE = 1.0
REQUIRED_MARK_PROTOCOL_COMPLIANCE = 1.0
REQUIRED_TARGET_COVERAGE = 0.9
REQUIRED_END_TO_END_ACCURACY = 0.7


def prediction_matches(class_id: int, prediction: str) -> bool:
    normalized = " ".join(re.sub(r"[^a-z0-9 ]+", " ", prediction.casefold()).split())
    tokens = set(normalized.split())
    for term in CLASS_TERMS[class_id]:
        normalized_term = " ".join(re.sub(r"[^a-z0-9 ]+", " ", term.casefold()).split())
        if " " in normalized_term and normalized_term in normalized:
            return True
        if normalized_term in tokens:
            return True
    return False


@dataclass(frozen=True, slots=True)
class ConditionCounters:
    condition: ExperimentCondition
    requested_images: int
    structured_output_valid_images: int
    mark_protocol_valid_images: int
    expected_targets: int
    returned_targets: int
    matched_targets: int
    hallucinated_mark_ids: int
    latencies_ms: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ConditionSummary:
    condition: ExperimentCondition
    requested_images: int
    structured_output_valid_images: int
    mark_protocol_valid_images: int
    expected_targets: int
    returned_targets: int
    matched_targets: int
    hallucinated_mark_ids: int
    structured_output_compliance: float
    mark_protocol_compliance: float | None
    target_coverage: float
    end_to_end_accuracy: float
    accuracy_when_returned: float | None
    mean_latency_ms: float
    gate_passed: bool | None


def build_condition_summary(counters: ConditionCounters) -> ConditionSummary:
    structured_output_compliance = (
        counters.structured_output_valid_images / counters.requested_images if counters.requested_images else 0.0
    )
    target_coverage = counters.returned_targets / counters.expected_targets if counters.expected_targets else 0.0
    end_to_end_accuracy = counters.matched_targets / counters.expected_targets if counters.expected_targets else 0.0
    match counters.condition:
        case ExperimentCondition.BASELINE:
            mark_protocol_compliance = None
            accuracy_when_returned = None
            gate_passed = None
        case ExperimentCondition.SOM_CONTROL | ExperimentCondition.DEPTH_GUIDED:
            mark_protocol_compliance = (
                counters.mark_protocol_valid_images / counters.requested_images if counters.requested_images else 0.0
            )
            accuracy_when_returned = (
                counters.matched_targets / counters.returned_targets if counters.returned_targets else 0.0
            )
            gate_passed = (
                structured_output_compliance >= REQUIRED_STRUCTURED_OUTPUT_COMPLIANCE
                and mark_protocol_compliance >= REQUIRED_MARK_PROTOCOL_COMPLIANCE
                and target_coverage >= REQUIRED_TARGET_COVERAGE
                and end_to_end_accuracy >= REQUIRED_END_TO_END_ACCURACY
                and counters.hallucinated_mark_ids == 0
            )
        case unreachable:
            assert_never(unreachable)
    return ConditionSummary(
        condition=counters.condition,
        requested_images=counters.requested_images,
        structured_output_valid_images=counters.structured_output_valid_images,
        mark_protocol_valid_images=counters.mark_protocol_valid_images,
        expected_targets=counters.expected_targets,
        returned_targets=counters.returned_targets,
        matched_targets=counters.matched_targets,
        hallucinated_mark_ids=counters.hallucinated_mark_ids,
        structured_output_compliance=round(structured_output_compliance, 4),
        mark_protocol_compliance=(
            round(mark_protocol_compliance, 4) if mark_protocol_compliance is not None else None
        ),
        target_coverage=round(target_coverage, 4),
        end_to_end_accuracy=round(end_to_end_accuracy, 4),
        accuracy_when_returned=(round(accuracy_when_returned, 4) if accuracy_when_returned is not None else None),
        mean_latency_ms=round(
            sum(counters.latencies_ms) / len(counters.latencies_ms) if counters.latencies_ms else 0.0,
            2,
        ),
        gate_passed=gate_passed,
    )
