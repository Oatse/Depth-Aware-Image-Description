from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from prototypes.depth_guided_roi_v3.models import RejectionReason, YoloBox


@dataclass(frozen=True, slots=True)
class QaThresholds:
    min_area: float
    min_side: float
    max_iou: float
    min_border_margin: float = 0.01


def audit_box(box: YoloBox, thresholds: QaThresholds) -> RejectionReason | None:
    left, top, right, bottom = box.raw_bounds()
    if left < 0.0 or top < 0.0 or right > 1.0 or bottom > 1.0:
        return RejectionReason.CLIPPED
    if min(left, top, 1.0 - right, 1.0 - bottom) < thresholds.min_border_margin:
        return RejectionReason.BORDER_TOUCHING
    if min(box.width, box.height) < thresholds.min_side:
        return RejectionReason.SMALL_SIDE
    if box.area < thresholds.min_area:
        return RejectionReason.SMALL_AREA
    return None


def intersection_over_union(first: YoloBox, second: YoloBox) -> float:
    first_left, first_top, first_right, first_bottom = first.raw_bounds()
    second_left, second_top, second_right, second_bottom = second.raw_bounds()
    intersection_width = max(0.0, min(first_right, second_right) - max(first_left, second_left))
    intersection_height = max(0.0, min(first_bottom, second_bottom) - max(first_top, second_top))
    intersection = intersection_width * intersection_height
    union = first.area + second.area - intersection
    return intersection / union if union > 0.0 else 0.0


def select_compatible_boxes(
    boxes: Sequence[YoloBox],
    thresholds: QaThresholds,
    limit: int,
) -> tuple[YoloBox, ...]:
    accepted = [box for box in boxes if audit_box(box, thresholds) is None]
    ordered = sorted(accepted, key=lambda box: (-box.area, box.class_id, box.center_x, box.center_y))
    selected: list[YoloBox] = []
    for candidate in ordered:
        if all(intersection_over_union(candidate, chosen) <= thresholds.max_iou for chosen in selected):
            selected.append(candidate)
        if len(selected) == limit:
            break
    return tuple(selected)
