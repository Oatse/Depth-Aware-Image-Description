from dataclasses import dataclass


REQUIRED_ANNOTATION_COLUMNS = {
    "image_name",
    "main_object",
    "object_position",
    "distance_category",
    "has_obstacle",
}
DEPTH_EVALUATED_MODES = frozenset({
    "all",
    "depth_only",
    "gemma_depth",
    "gemma_depth_legacy_controlled",
    "gemma_depth_constrained_controlled",
    "grid_p10",
})
SEMANTIC_EVALUATED_MODES = frozenset({
    "all",
    "gemma_only",
    "gemma_depth",
    "gemma_depth_legacy_controlled",
    "gemma_depth_constrained_controlled",
})


@dataclass(frozen=True, slots=True)
class IoTEvaluationSummary:
    capture_count: int
    pairing_coverage: float
    partial_rate: float
    conflict_rate: float
    stale_rate: float
    mean_timestamp_offset_ms: float | None
    mean_sensor_disagreement_cm: float | None
    absolute_error_cm: float | None
    sensor_depth_consistency_accuracy: float | None
    latency_overhead_ms: float | None
    description_quality_delta: float | None


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    total_images: int
    prediction_coverage: float
    object_accuracy: float | None
    position_accuracy: float | None
    object_position_joint_accuracy: float | None
    distance_category_accuracy: float | None
    obstacle_warning_accuracy: float | None
    obstacle_precision: float | None
    obstacle_recall: float | None
    obstacle_f1: float | None
    obstacle_true_positive: int | None
    obstacle_false_positive: int | None
    obstacle_true_negative: int | None
    obstacle_false_negative: int | None
    average_latency_ms: float
