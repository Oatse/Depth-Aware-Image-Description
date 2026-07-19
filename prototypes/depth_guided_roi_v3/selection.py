from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from prototypes.depth_guided_roi_v3.models import RegionMark, YoloBox


def _finite_region(depth_map: np.ndarray, box: YoloBox) -> np.ndarray:
    height, width = depth_map.shape
    left, top, right, bottom = box.raw_bounds()
    inset_x = box.width * 0.1
    inset_y = box.height * 0.1
    x1 = max(0, min(width - 1, math.floor((left + inset_x) * width)))
    y1 = max(0, min(height - 1, math.floor((top + inset_y) * height)))
    x2 = max(x1 + 1, min(width, math.ceil((right - inset_x) * width)))
    y2 = max(y1 + 1, min(height, math.ceil((bottom - inset_y) * height)))
    values = depth_map[y1:y2, x1:x2]
    return values[np.isfinite(values)]


def filter_depth_stable_boxes(
    depth_map: np.ndarray,
    boxes: Sequence[YoloBox],
    max_relative_spread: float,
) -> tuple[YoloBox, ...]:
    if depth_map.ndim != 2:
        return ()
    stable: list[YoloBox] = []
    for box in boxes:
        finite = _finite_region(depth_map, box)
        if finite.size == 0:
            continue
        median = float(np.median(finite))
        spread = float(np.percentile(finite, 90) - np.percentile(finite, 10)) / max(abs(median), 1e-6)
        if spread <= max_relative_spread:
            stable.append(box)
    return tuple(stable)


def select_control_marks(boxes: Sequence[YoloBox], limit: int) -> tuple[RegionMark, ...]:
    selected = sorted(boxes, key=lambda box: (-box.area, box.class_id, box.center_x, box.center_y))[:limit]
    return tuple(
        RegionMark(mark_id=index, box=box, median_depth=None, p10_depth=None)
        for index, box in enumerate(selected, start=1)
    )


def select_depth_marks(
    depth_map: np.ndarray,
    boxes: Sequence[YoloBox],
    limit: int,
) -> tuple[RegionMark, ...]:
    if depth_map.ndim != 2:
        return ()
    scored: list[tuple[float, float, YoloBox]] = []
    for box in boxes:
        finite = _finite_region(depth_map, box)
        if finite.size > 0:
            scored.append((float(np.median(finite)), float(np.percentile(finite, 10)), box))
    scored.sort(key=lambda item: (item[0], item[1], item[2].class_id))
    return tuple(
        RegionMark(mark_id=index, box=box, median_depth=median, p10_depth=p10)
        for index, (median, p10, box) in enumerate(scored[:limit], start=1)
    )
