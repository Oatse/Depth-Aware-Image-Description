from __future__ import annotations

import numpy as np

from prototypes.depth_guided_roi_v3.geometry_qa import (
    QaThresholds,
    audit_box,
    intersection_over_union,
    select_compatible_boxes,
)
from prototypes.depth_guided_roi_v3.metrics import ConditionCounters, build_condition_summary, prediction_matches
from prototypes.depth_guided_roi_v3.models import ExperimentCondition, RejectionReason, YoloBox
from prototypes.depth_guided_roi_v3.protocol import MarkAnswer, MarkedResponse, has_exact_mark_ids
from prototypes.depth_guided_roi_v3.selection import (
    filter_depth_stable_boxes,
    select_control_marks,
    select_depth_marks,
)


def _box(
    class_id: int,
    center_x: float,
    center_y: float,
    width: float,
    height: float,
) -> YoloBox:
    return YoloBox(
        class_id=class_id,
        center_x=center_x,
        center_y=center_y,
        width=width,
        height=height,
    )


def test_audit_box_rejects_geometry_risks_when_annotation_is_clipped_or_small() -> None:
    # Given
    thresholds = QaThresholds(min_area=0.015, min_side=0.06, max_iou=0.15)
    clipped = _box(1, 0.03, 0.50, 0.10, 0.30)
    small = _box(2, 0.50, 0.50, 0.05, 0.20)
    clean = _box(3, 0.50, 0.50, 0.30, 0.30)

    # When
    clipped_result = audit_box(clipped, thresholds)
    small_result = audit_box(small, thresholds)
    clean_result = audit_box(clean, thresholds)

    # Then
    assert clipped_result == RejectionReason.CLIPPED
    assert small_result == RejectionReason.SMALL_SIDE
    assert clean_result is None


def test_audit_box_rejects_box_that_touches_image_border() -> None:
    # Given
    thresholds = QaThresholds(min_area=0.015, min_side=0.06, max_iou=0.15, min_border_margin=0.01)
    border_touching = _box(1, 0.10, 0.50, 0.20, 0.30)

    # When
    result = audit_box(border_touching, thresholds)

    # Then
    assert result == RejectionReason.BORDER_TOUCHING


def test_select_compatible_boxes_excludes_overlapping_candidates() -> None:
    # Given
    thresholds = QaThresholds(min_area=0.015, min_side=0.06, max_iou=0.15)
    large = _box(1, 0.30, 0.50, 0.35, 0.40)
    overlapping = _box(2, 0.35, 0.50, 0.30, 0.35)
    right = _box(3, 0.75, 0.50, 0.25, 0.30)

    # When
    selected = select_compatible_boxes((large, overlapping, right), thresholds, limit=3)

    # Then
    assert selected == (large, right)
    assert intersection_over_union(large, overlapping) > thresholds.max_iou


def test_control_selection_uses_area_and_not_depth_values() -> None:
    # Given
    small_left = _box(1, 0.20, 0.50, 0.20, 0.20)
    large_middle = _box(2, 0.50, 0.50, 0.30, 0.30)
    medium_right = _box(3, 0.80, 0.50, 0.25, 0.25)

    # When
    marks = select_control_marks((small_left, large_middle, medium_right), limit=2)

    # Then
    assert tuple(mark.box for mark in marks) == (large_middle, medium_right)
    assert tuple(mark.mark_id for mark in marks) == (1, 2)


def test_depth_selection_prefers_lower_median_depth() -> None:
    # Given
    left = _box(1, 0.25, 0.50, 0.30, 0.40)
    right = _box(2, 0.75, 0.50, 0.30, 0.40)
    depth_map = np.full((100, 100), 8.0, dtype=np.float32)
    depth_map[30:70, 60:90] = 1.0

    # When
    marks = select_depth_marks(depth_map, (left, right), limit=2)

    # Then
    assert tuple(mark.box for mark in marks) == (right, left)
    assert marks[0].median_depth < marks[1].median_depth


def test_variance_filter_rejects_region_with_mixed_depth_surfaces() -> None:
    # Given
    stable = _box(1, 0.25, 0.50, 0.30, 0.40)
    mixed = _box(2, 0.75, 0.50, 0.30, 0.40)
    depth_map = np.full((100, 100), 4.0, dtype=np.float32)
    depth_map[30:50, 60:90] = 1.0
    depth_map[50:70, 60:90] = 8.0

    # When
    filtered = filter_depth_stable_boxes(depth_map, (stable, mixed), max_relative_spread=0.5)

    # Then
    assert filtered == (stable,)


def test_condition_summary_keeps_schema_failure_separate_from_grounding_error() -> None:
    # Given
    counters = ConditionCounters(
        condition=ExperimentCondition.DEPTH_GUIDED,
        requested_images=2,
        structured_output_valid_images=2,
        mark_protocol_valid_images=1,
        expected_targets=6,
        returned_targets=3,
        matched_targets=2,
        hallucinated_mark_ids=0,
        latencies_ms=(100, 120),
    )

    # When
    summary = build_condition_summary(counters)

    # Then
    assert summary.structured_output_compliance == 1.0
    assert summary.mark_protocol_compliance == 0.5
    assert summary.target_coverage == 0.5
    assert summary.end_to_end_accuracy == 0.3333
    assert summary.accuracy_when_returned == 0.6667
    assert not summary.gate_passed


def test_baseline_summary_marks_region_protocol_metrics_as_not_applicable() -> None:
    # Given
    counters = ConditionCounters(
        condition=ExperimentCondition.BASELINE,
        requested_images=2,
        structured_output_valid_images=2,
        mark_protocol_valid_images=2,
        expected_targets=5,
        returned_targets=3,
        matched_targets=3,
        hallucinated_mark_ids=0,
        latencies_ms=(100, 120),
    )

    # When
    summary = build_condition_summary(counters)

    # Then
    assert summary.mark_protocol_compliance is None
    assert summary.accuracy_when_returned is None
    assert summary.gate_passed is None


def test_mark_response_requires_each_expected_id_exactly_once() -> None:
    # Given
    complete = MarkedResponse(
        marks=(
            MarkAnswer(id=1, object="meja"),
            MarkAnswer(id=2, object="kursi"),
            MarkAnswer(id=3, object="lampu"),
        ),
        priority_mark_id=1,
        description="Meja, kursi, dan lampu terlihat pada region bertanda.",
    )
    duplicate = MarkedResponse(
        marks=(
            MarkAnswer(id=1, object="meja"),
            MarkAnswer(id=1, object="kursi"),
            MarkAnswer(id=3, object="lampu"),
        ),
        priority_mark_id=1,
        description="Respons memiliki ID ganda.",
    )

    # When
    complete_is_valid = has_exact_mark_ids(complete, (1, 2, 3))
    duplicate_is_valid = has_exact_mark_ids(duplicate, (1, 2, 3))

    # Then
    assert complete_is_valid
    assert not duplicate_is_valid


def test_prediction_matcher_accepts_specific_synonyms_but_rejects_generic_seating() -> None:
    # Given
    laptop_class_id = 6
    sofa_class_id = 1
    potted_plant_class_id = 10

    # When
    notebook_matches = prediction_matches(laptop_class_id, "sebuah notebook")
    generic_seating_matches = prediction_matches(sofa_class_id, "tempat duduk merah")
    plant_matches = prediction_matches(potted_plant_class_id, "plant")

    # Then
    assert notebook_matches
    assert not generic_seating_matches
    assert plant_matches
