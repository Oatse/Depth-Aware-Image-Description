from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Sequence, assert_never

from pydantic import BaseModel, ConfigDict, ValidationError

from app.config import Settings
from prototypes.depth_guided_roi_v3.inference import StructuredRequest, infer_structured
from prototypes.depth_guided_roi_v3.metrics import prediction_matches
from prototypes.depth_guided_roi_v3.models import CLASS_NAMES, ExperimentCondition, StoredInference
from prototypes.depth_guided_roi_v3.protocol import MarkedResponse, has_exact_mark_ids, prompt_for
from prototypes.depth_guided_roi_v3.strong_model_protocol import parse_marked_response
from prototypes.depth_guided_roi_v3.strong_model_reporting import (
    PairOutcome,
    diagnostic_verdict,
    summarize_pairs,
)
from services.image_preprocess import preprocess_image


class FrozenMarkRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    image_name: str
    condition: ExperimentCondition
    mark_id: int
    expected_class: str
    object_match: bool


@dataclass(frozen=True, slots=True)
class DiagnosticCase:
    image_name: str
    condition: ExperimentCondition
    image_path: Path
    expected_marks: tuple[FrozenMarkRow, ...]


@dataclass(frozen=True, slots=True)
class StrongMarkResult:
    image_name: str
    condition: ExperimentCondition
    mark_id: int
    expected_class: str
    predicted_object: str
    object_match: bool


@dataclass(frozen=True, slots=True)
class StrongObservation:
    image_name: str
    condition: ExperimentCondition
    raw_schema_valid: bool
    canonical_protocol_valid: bool
    expected_targets: int
    returned_targets: int
    matched_targets: int
    latency_ms: int


@dataclass(frozen=True, slots=True)
class DiagnosticBundle:
    observations: tuple[StrongObservation, ...]
    mark_results: tuple[StrongMarkResult, ...]
    source_rows: tuple[FrozenMarkRow, ...]


@dataclass(frozen=True, slots=True)
class DiagnosticArtifactError(Exception):
    reason: str

    def __str__(self) -> str:
        return self.reason


def _marked_image_path(source_root: Path, row: FrozenMarkRow) -> Path:
    stem = Path(row.image_name).stem
    match row.condition:
        case ExperimentCondition.SOM_CONTROL:
            return source_root / "som_control" / f"{stem}_control.jpg"
        case ExperimentCondition.DEPTH_GUIDED:
            return source_root / "depth_guided" / f"{stem}_depth_guided.jpg"
        case ExperimentCondition.BASELINE:
            raise DiagnosticArtifactError("Baseline rows are outside the marked model-swap diagnostic.")
        case unreachable:
            assert_never(unreachable)


def load_frozen_cases(source_root: Path) -> tuple[DiagnosticCase, ...]:
    source_csv = source_root / "mark_results.csv"
    with source_csv.open(newline="", encoding="utf-8") as handle:
        rows = tuple(FrozenMarkRow.model_validate(row) for row in csv.DictReader(handle))
    grouped: dict[tuple[str, ExperimentCondition], list[FrozenMarkRow]] = {}
    for row in rows:
        grouped.setdefault((row.image_name, row.condition), []).append(row)
    cases: list[DiagnosticCase] = []
    for (image_name, condition), expected_marks in grouped.items():
        ordered = tuple(sorted(expected_marks, key=lambda mark: mark.mark_id))
        image_path = _marked_image_path(source_root, ordered[0])
        if len(ordered) != 3 or not image_path.is_file():
            raise DiagnosticArtifactError(f"Frozen case is incomplete: {condition.value}/{image_name}")
        cases.append(DiagnosticCase(image_name, condition, image_path, ordered))
    return tuple(sorted(cases, key=lambda case: (case.image_name, case.condition.value)))


async def _load_or_infer(
    settings: Settings,
    output_root: Path,
    case: DiagnosticCase,
) -> StoredInference:
    cache_path = output_root / "responses" / case.condition.value / f"{Path(case.image_name).stem}.json"
    if cache_path.exists():
        return StoredInference.model_validate_json(cache_path.read_text(encoding="utf-8"))
    processed = preprocess_image(case.image_path.read_bytes(), settings.image_max_dimension)
    result = await infer_structured(
        settings,
        StructuredRequest(
            image_base64=processed.base64_image,
            prompt=prompt_for(case.condition, tuple(mark.mark_id for mark in case.expected_marks)),
            schema_name=f"strong_{case.condition.value}_response",
            response_model=MarkedResponse,
        ),
    )
    stored = StoredInference(
        image_name=case.image_name,
        condition=case.condition,
        content=result.content,
        latency_ms=result.latency_ms,
    )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(stored.model_dump_json(indent=2), encoding="utf-8")
    return stored


def _evaluate(case: DiagnosticCase, stored: StoredInference) -> tuple[StrongObservation, tuple[StrongMarkResult, ...]]:
    try:
        response = MarkedResponse.model_validate_json(stored.content)
        raw_schema_valid = True
    except ValidationError:
        response = parse_marked_response(stored.content)
        raw_schema_valid = False
    expected_ids = tuple(mark.mark_id for mark in case.expected_marks)
    answers = {answer.mark_id: answer.object_name for answer in response.marks}
    results: list[StrongMarkResult] = []
    for mark in case.expected_marks:
        prediction = answers.get(mark.mark_id, "tidak_dikembalikan")
        class_id = CLASS_NAMES.index(mark.expected_class)
        results.append(
            StrongMarkResult(
                image_name=case.image_name,
                condition=case.condition,
                mark_id=mark.mark_id,
                expected_class=mark.expected_class,
                predicted_object=prediction,
                object_match=prediction_matches(class_id, prediction),
            )
        )
    return (
        StrongObservation(
            image_name=case.image_name,
            condition=case.condition,
            raw_schema_valid=raw_schema_valid,
            canonical_protocol_valid=has_exact_mark_ids(response, expected_ids),
            expected_targets=len(expected_ids),
            returned_targets=len(set(answers) & set(expected_ids)),
            matched_targets=sum(result.object_match for result in results),
            latency_ms=stored.latency_ms,
        ),
        tuple(results),
    )


async def run_diagnostic(settings: Settings, source_root: Path, output_root: Path) -> DiagnosticBundle:
    cases = load_frozen_cases(source_root)
    observations: list[StrongObservation] = []
    mark_results: list[StrongMarkResult] = []
    for index, case in enumerate(cases, start=1):
        stored = await _load_or_infer(settings, output_root, case)
        observation, results = _evaluate(case, stored)
        observations.append(observation)
        mark_results.extend(results)
        print(f"{index}/{len(cases)} | {case.condition.value} | {case.image_name}", flush=True)
    return DiagnosticBundle(tuple(observations), tuple(mark_results), tuple(mark for case in cases for mark in case.expected_marks))


def _write_csv(path: Path, rows: Sequence[StrongObservation] | Sequence[StrongMarkResult]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[field.name for field in fields(rows[0])])
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def write_diagnostic(output_root: Path, bundle: DiagnosticBundle, model: str) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(output_root / "condition_observations.csv", bundle.observations)
    _write_csv(output_root / "mark_results.csv", bundle.mark_results)
    source_by_key = {(row.image_name, row.condition, row.mark_id): row.object_match for row in bundle.source_rows}
    outcomes = tuple(
        PairOutcome(result.condition, source_by_key[(result.image_name, result.condition, result.mark_id)], result.object_match)
        for result in bundle.mark_results
    )
    conditions = (ExperimentCondition.SOM_CONTROL, ExperimentCondition.DEPTH_GUIDED)
    paired = tuple(summarize_pairs(outcomes, condition) for condition in conditions)
    verdict = diagnostic_verdict(paired)
    observations_by_condition = {
        condition: tuple(row for row in bundle.observations if row.condition is condition) for condition in conditions
    }
    report = {
        "model_route": model,
        "same_frozen_marked_images": True,
        "conditions": [
            {
                **asdict(summary),
                "raw_schema_compliance": round(
                    sum(row.raw_schema_valid for row in observations_by_condition[summary.condition])
                    / len(observations_by_condition[summary.condition]),
                    4,
                ),
                "canonical_protocol_compliance": round(
                    sum(row.canonical_protocol_valid for row in observations_by_condition[summary.condition])
                    / len(observations_by_condition[summary.condition]),
                    4,
                ),
                "identity_gate_passed": summary.strong_accuracy >= 0.7,
            }
            for summary in paired
        ],
        "verdict": {
            **asdict(verdict),
            "raw_schema_adapter_required": any(not row.raw_schema_valid for row in bundle.observations),
        },
    }
    (output_root / "paired_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
