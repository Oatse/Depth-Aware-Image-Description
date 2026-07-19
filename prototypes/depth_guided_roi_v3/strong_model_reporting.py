from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from prototypes.depth_guided_roi_v3.models import ExperimentCondition


@dataclass(frozen=True, slots=True)
class PairOutcome:
    condition: ExperimentCondition
    gemma_correct: bool
    strong_correct: bool


@dataclass(frozen=True, slots=True)
class PairSummary:
    condition: ExperimentCondition
    total_marks: int
    gemma_correct: int
    strong_correct: int
    both_correct: int
    both_wrong: int
    gemma_wrong_strong_correct: int
    gemma_correct_strong_wrong: int
    gemma_accuracy: float
    strong_accuracy: float
    accuracy_delta: float


@dataclass(frozen=True, slots=True)
class DiagnosticVerdict:
    stronger_model_improved_both_conditions: bool
    model_alone_explains_failure: bool
    depth_selection_benefit_proven: bool = False


def summarize_pairs(outcomes: Sequence[PairOutcome], condition: ExperimentCondition) -> PairSummary:
    selected = tuple(outcome for outcome in outcomes if outcome.condition is condition)
    total = len(selected)
    gemma_correct = sum(outcome.gemma_correct for outcome in selected)
    strong_correct = sum(outcome.strong_correct for outcome in selected)
    both_correct = sum(outcome.gemma_correct and outcome.strong_correct for outcome in selected)
    both_wrong = sum(not outcome.gemma_correct and not outcome.strong_correct for outcome in selected)
    gains = sum(not outcome.gemma_correct and outcome.strong_correct for outcome in selected)
    losses = sum(outcome.gemma_correct and not outcome.strong_correct for outcome in selected)
    gemma_accuracy = gemma_correct / total if total else 0.0
    strong_accuracy = strong_correct / total if total else 0.0
    return PairSummary(
        condition=condition,
        total_marks=total,
        gemma_correct=gemma_correct,
        strong_correct=strong_correct,
        both_correct=both_correct,
        both_wrong=both_wrong,
        gemma_wrong_strong_correct=gains,
        gemma_correct_strong_wrong=losses,
        gemma_accuracy=round(gemma_accuracy, 4),
        strong_accuracy=round(strong_accuracy, 4),
        accuracy_delta=round(strong_accuracy - gemma_accuracy, 4),
    )


def diagnostic_verdict(summaries: Sequence[PairSummary]) -> DiagnosticVerdict:
    return DiagnosticVerdict(
        stronger_model_improved_both_conditions=all(summary.accuracy_delta > 0.0 for summary in summaries),
        model_alone_explains_failure=all(summary.strong_accuracy >= 0.7 for summary in summaries),
    )
