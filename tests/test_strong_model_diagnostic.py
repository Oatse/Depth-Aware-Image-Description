from __future__ import annotations

from prototypes.depth_guided_roi_v3.strong_model_protocol import parse_marked_response
from prototypes.depth_guided_roi_v3.strong_model_reporting import (
    PairOutcome,
    diagnostic_verdict,
    summarize_pairs,
)
from prototypes.depth_guided_roi_v3.models import ExperimentCondition


def test_parse_marked_response_accepts_flat_mark_keys_from_router() -> None:
    # Given
    content = '{"MARK 1":"coffee table","MARK 2":"door","MARK 3":"window","priority_mark_id":"MARK 2"}'

    # When
    response = parse_marked_response(content)

    # Then
    assert tuple((answer.mark_id, answer.object_name) for answer in response.marks) == (
        (1, "coffee table"),
        (2, "door"),
        (3, "window"),
    )
    assert response.priority_mark_id == 2


def test_parse_marked_response_accepts_objects_map_from_router() -> None:
    # Given
    content = '{"priority_mark_id":1,"objects":{"1":"coffee table","2":"chair","3":"drawer cabinet"}}'

    # When
    response = parse_marked_response(content)

    # Then
    assert tuple((answer.mark_id, answer.object_name) for answer in response.marks) == (
        (1, "coffee table"),
        (2, "chair"),
        (3, "drawer cabinet"),
    )
    assert response.priority_mark_id == 1


def test_parse_marked_response_accepts_marks_map_from_router() -> None:
    # Given
    content = '{"priority_mark_id":1,"marks":{"1":"side table","2":"armchair","3":"vase"}}'

    # When
    response = parse_marked_response(content)

    # Then
    assert tuple((answer.mark_id, answer.object_name) for answer in response.marks) == (
        (1, "side table"),
        (2, "armchair"),
        (3, "vase"),
    )


def test_parse_marked_response_accepts_standard_marks_without_description() -> None:
    # Given
    content = (
        '{"priority_mark_id":1,"marks":['
        '{"id":1,"object":"side table"},'
        '{"id":2,"object":"armchair"},'
        '{"id":3,"object":"coffee table"}]}'
    )

    # When
    response = parse_marked_response(content)

    # Then
    assert tuple(answer.mark_id for answer in response.marks) == (1, 2, 3)
    assert response.description.startswith("Normalized router response")


def test_parse_marked_response_accepts_flat_numeric_keys_from_router() -> None:
    # Given
    content = '{"1":"sofa","2":"side table","3":"coffee table","priority_mark_id":1}'

    # When
    response = parse_marked_response(content)

    # Then
    assert tuple((answer.mark_id, answer.object_name) for answer in response.marks) == (
        (1, "sofa"),
        (2, "side table"),
        (3, "coffee table"),
    )


def test_parse_marked_response_accepts_objects_list_from_router() -> None:
    # Given
    content = (
        '{"priority_mark_id":1,"objects":['
        '{"id":1,"object":"TV"},'
        '{"id":2,"object":"cabinet"},'
        '{"id":3,"object":"plant"}]}'
    )

    # When
    response = parse_marked_response(content)

    # Then
    assert tuple(answer.object_name for answer in response.marks) == ("TV", "cabinet", "plant")


def test_summarize_pairs_counts_model_gains_and_losses_per_condition() -> None:
    # Given
    outcomes = (
        PairOutcome(ExperimentCondition.SOM_CONTROL, gemma_correct=False, strong_correct=True),
        PairOutcome(ExperimentCondition.SOM_CONTROL, gemma_correct=False, strong_correct=True),
        PairOutcome(ExperimentCondition.SOM_CONTROL, gemma_correct=True, strong_correct=False),
        PairOutcome(ExperimentCondition.SOM_CONTROL, gemma_correct=True, strong_correct=True),
    )

    # When
    summary = summarize_pairs(outcomes, ExperimentCondition.SOM_CONTROL)

    # Then
    assert summary.total_marks == 4
    assert summary.gemma_correct == 2
    assert summary.strong_correct == 3
    assert summary.gemma_wrong_strong_correct == 2
    assert summary.gemma_correct_strong_wrong == 1
    assert summary.accuracy_delta == 0.25


def test_diagnostic_verdict_separates_improvement_from_sufficient_explanation() -> None:
    # Given
    control = summarize_pairs(
        (
            PairOutcome(ExperimentCondition.SOM_CONTROL, False, True),
            PairOutcome(ExperimentCondition.SOM_CONTROL, True, False),
            PairOutcome(ExperimentCondition.SOM_CONTROL, False, True),
            PairOutcome(ExperimentCondition.SOM_CONTROL, False, False),
        ),
        ExperimentCondition.SOM_CONTROL,
    )
    depth = summarize_pairs(
        (
            PairOutcome(ExperimentCondition.DEPTH_GUIDED, False, True),
            PairOutcome(ExperimentCondition.DEPTH_GUIDED, True, True),
            PairOutcome(ExperimentCondition.DEPTH_GUIDED, False, False),
            PairOutcome(ExperimentCondition.DEPTH_GUIDED, False, False),
        ),
        ExperimentCondition.DEPTH_GUIDED,
    )

    # When
    verdict = diagnostic_verdict((control, depth))

    # Then
    assert verdict.stronger_model_improved_both_conditions
    assert not verdict.model_alone_explains_failure
