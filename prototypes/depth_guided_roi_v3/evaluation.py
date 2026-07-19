from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, assert_never

from pydantic import BaseModel, ValidationError

from app.config import Settings
from prototypes.depth_guided_roi_v3.inference import (
    GemmaResponseError,
    StructuredRequest,
    infer_structured,
)
from prototypes.depth_guided_roi_v3.metrics import prediction_matches
from prototypes.depth_guided_roi_v3.models import (
    CLASS_NAMES,
    ConditionObservation,
    ExperimentCondition,
    ExperimentConfig,
    MarkObservation,
    PreparedSample,
    RegionMark,
    StoredInference,
)
from prototypes.depth_guided_roi_v3.protocol import (
    BaselineResponse,
    MarkedResponse,
    has_exact_mark_ids,
    prompt_for,
)
from services.image_preprocess import preprocess_image


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    settings: Settings
    config: ExperimentConfig


@dataclass(frozen=True, slots=True)
class InferenceCase:
    image_name: str
    condition: ExperimentCondition
    image_path: Path
    marks: tuple[RegionMark, ...]
    response_model: type[BaseModel]


@dataclass(frozen=True, slots=True)
class EvaluationBundle:
    observations: tuple[ConditionObservation, ...]
    mark_rows: tuple[MarkObservation, ...]


def _cases_for(sample: PreparedSample) -> tuple[InferenceCase, ...]:
    return (
        InferenceCase(
            image_name=sample.sample.image_path.name,
            condition=ExperimentCondition.BASELINE,
            image_path=sample.baseline_path,
            marks=sample.depth_marks,
            response_model=BaselineResponse,
        ),
        InferenceCase(
            image_name=sample.sample.image_path.name,
            condition=ExperimentCondition.SOM_CONTROL,
            image_path=sample.control_path,
            marks=sample.control_marks,
            response_model=MarkedResponse,
        ),
        InferenceCase(
            image_name=sample.sample.image_path.name,
            condition=ExperimentCondition.DEPTH_GUIDED,
            image_path=sample.depth_guided_path,
            marks=sample.depth_marks,
            response_model=MarkedResponse,
        ),
    )


async def _load_or_infer(context: EvaluationContext, case: InferenceCase) -> StoredInference:
    cache_dir = context.config.paths.output_root / "responses" / case.condition.value
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{Path(case.image_name).stem}.json"
    if cache_path.exists():
        return StoredInference.model_validate_json(cache_path.read_text(encoding="utf-8"))

    processed = preprocess_image(case.image_path.read_bytes(), context.settings.image_max_dimension)
    mark_ids = tuple(mark.mark_id for mark in case.marks)
    result = await infer_structured(
        context.settings,
        StructuredRequest(
            image_base64=processed.base64_image,
            prompt=prompt_for(case.condition, mark_ids),
            schema_name=f"{case.condition.value}_response",
            response_model=case.response_model,
        ),
    )
    stored = StoredInference(
        image_name=case.image_name,
        condition=case.condition,
        content=result.content,
        latency_ms=result.latency_ms,
    )
    cache_path.write_text(stored.model_dump_json(indent=2), encoding="utf-8")
    return stored


def _evaluate_baseline(case: InferenceCase, stored: StoredInference) -> ConditionObservation:
    response = BaselineResponse.model_validate_json(stored.content)
    expected_class_ids = tuple(sorted({mark.box.class_id for mark in case.marks}))
    matched = sum(
        any(prediction_matches(class_id, prediction) for prediction in response.objects)
        for class_id in expected_class_ids
    )
    return ConditionObservation(
        image_name=case.image_name,
        condition=case.condition,
        structured_output_valid=True,
        mark_protocol_valid=True,
        expected_targets=len(expected_class_ids),
        returned_targets=matched,
        matched_targets=matched,
        hallucinated_mark_ids=0,
        latency_ms=stored.latency_ms,
        error=None,
    )


def _evaluate_marked(
    case: InferenceCase,
    stored: StoredInference,
) -> tuple[ConditionObservation, tuple[MarkObservation, ...]]:
    response = MarkedResponse.model_validate_json(stored.content)
    expected_ids = tuple(mark.mark_id for mark in case.marks)
    exact_ids = has_exact_mark_ids(response, expected_ids)
    answers = {answer.mark_id: answer.object_name for answer in response.marks}
    returned_ids = set(answers) & set(expected_ids)
    hallucinated = len(set(answers) - set(expected_ids))
    rows: list[MarkObservation] = []
    matched = 0
    for mark in case.marks:
        prediction = answers.get(mark.mark_id, "tidak_dikembalikan")
        object_match = prediction_matches(mark.box.class_id, prediction)
        matched += int(object_match)
        rows.append(
            MarkObservation(
                image_name=case.image_name,
                condition=case.condition,
                mark_id=mark.mark_id,
                expected_class=CLASS_NAMES[mark.box.class_id],
                predicted_object=prediction,
                object_match=object_match,
                median_depth=mark.median_depth,
                p10_depth=mark.p10_depth,
            )
        )
    return (
        ConditionObservation(
            image_name=case.image_name,
            condition=case.condition,
            structured_output_valid=True,
            mark_protocol_valid=exact_ids,
            expected_targets=len(expected_ids),
            returned_targets=len(returned_ids),
            matched_targets=matched,
            hallucinated_mark_ids=hallucinated,
            latency_ms=stored.latency_ms,
            error=None if exact_ids else "mark IDs were missing or duplicated",
        ),
        tuple(rows),
    )


def _failure_observation(case: InferenceCase, reason: str) -> ConditionObservation:
    return ConditionObservation(
        image_name=case.image_name,
        condition=case.condition,
        structured_output_valid=False,
        mark_protocol_valid=False,
        expected_targets=len({mark.box.class_id for mark in case.marks})
        if case.condition is ExperimentCondition.BASELINE
        else len(case.marks),
        returned_targets=0,
        matched_targets=0,
        hallucinated_mark_ids=0,
        latency_ms=0,
        error=reason,
    )


async def evaluate_prepared(
    context: EvaluationContext,
    prepared_samples: Sequence[PreparedSample],
) -> EvaluationBundle:
    observations: list[ConditionObservation] = []
    mark_rows: list[MarkObservation] = []
    for prepared in prepared_samples:
        for case in _cases_for(prepared):
            try:
                stored = await _load_or_infer(context, case)
                match case.condition:
                    case ExperimentCondition.BASELINE:
                        observations.append(_evaluate_baseline(case, stored))
                    case ExperimentCondition.SOM_CONTROL | ExperimentCondition.DEPTH_GUIDED:
                        observation, rows = _evaluate_marked(case, stored)
                        observations.append(observation)
                        mark_rows.extend(rows)
                    case unreachable:
                        assert_never(unreachable)
            except (GemmaResponseError, ValidationError, OSError, ValueError) as exc:
                observations.append(_failure_observation(case, str(exc)))
                error_dir = context.config.paths.output_root / "errors"
                error_dir.mkdir(parents=True, exist_ok=True)
                (error_dir / f"{Path(case.image_name).stem}_{case.condition.value}.json").write_text(
                    json.dumps(
                        {"image": case.image_name, "condition": case.condition.value, "error": str(exc)},
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
    return EvaluationBundle(observations=tuple(observations), mark_rows=tuple(mark_rows))
