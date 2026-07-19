from __future__ import annotations

import csv
import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Sequence

from prototypes.depth_guided_roi_v3.evaluation import EvaluationBundle
from prototypes.depth_guided_roi_v3.metrics import ConditionCounters, ConditionSummary, build_condition_summary
from prototypes.depth_guided_roi_v3.models import ConditionObservation, ExperimentCondition, MarkObservation


def _summarize_condition(
    condition: ExperimentCondition,
    observations: Sequence[ConditionObservation],
) -> ConditionSummary:
    selected = tuple(observation for observation in observations if observation.condition is condition)
    return build_condition_summary(
        ConditionCounters(
            condition=condition,
            requested_images=len(selected),
            structured_output_valid_images=sum(observation.structured_output_valid for observation in selected),
            mark_protocol_valid_images=sum(observation.mark_protocol_valid for observation in selected),
            expected_targets=sum(observation.expected_targets for observation in selected),
            returned_targets=sum(observation.returned_targets for observation in selected),
            matched_targets=sum(observation.matched_targets for observation in selected),
            hallucinated_mark_ids=sum(observation.hallucinated_mark_ids for observation in selected),
            latencies_ms=tuple(observation.latency_ms for observation in selected if observation.latency_ms > 0),
        )
    )


def _write_csv(path: Path, rows: Sequence[ConditionObservation] | Sequence[MarkObservation]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[field.name for field in fields(rows[0])])
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_report(output_root: Path, bundle: EvaluationBundle) -> dict[str, bool | str]:
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(output_root / "condition_observations.csv", bundle.observations)
    _write_csv(output_root / "mark_results.csv", bundle.mark_rows)
    summaries = tuple(
        _summarize_condition(condition, bundle.observations)
        for condition in ExperimentCondition
    )
    summary_by_condition = {summary.condition: summary for summary in summaries}
    mark_grounding_gate = (
        summary_by_condition[ExperimentCondition.SOM_CONTROL].gate_passed is True
        and summary_by_condition[ExperimentCondition.DEPTH_GUIDED].gate_passed is True
    )
    verdict = {
        "mark_grounding_gate_passed": mark_grounding_gate,
        "depth_selection_benefit_proven": False,
        "detector_training_allowed": False,
        "reason": (
            "Mark grounding passed, but HomeObjects-3K has no reference depth; detector training remains blocked for the depth-benefit claim."
            if mark_grounding_gate
            else "Mark grounding failed under oracle boxes; detector training is blocked."
        ),
    }
    (output_root / "summary.json").write_text(
        json.dumps(
            {
                "conditions": [asdict(summary) for summary in summaries],
                "verdict": verdict,
                "metric_scope": {
                    "baseline": "recall of classes selected by the depth-guided oracle-box condition",
                    "marked_conditions": "region identity accuracy against HomeObjects-3K object labels",
                    "depth": "model-estimated relative ordering only; no physical depth ground truth",
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return verdict
