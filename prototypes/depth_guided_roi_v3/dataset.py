from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from prototypes.depth_guided_roi_v3.geometry_qa import QaThresholds, audit_box, select_compatible_boxes
from prototypes.depth_guided_roi_v3.models import (
    CLASS_NAMES,
    DatasetAudit,
    DatasetSample,
    RejectionReason,
    SampleSelection,
    YoloBox,
)


@dataclass(frozen=True, slots=True)
class AnnotationFormatError(Exception):
    path: Path
    line_number: int
    content: str

    def __str__(self) -> str:
        return f"Invalid YOLO annotation at {self.path}:{self.line_number}: {self.content!r}"


@dataclass(frozen=True, slots=True)
class SelectionPolicy:
    limit: int
    thresholds: QaThresholds
    excluded_names: frozenset[str]


def parse_yolo_labels(path: Path) -> tuple[YoloBox, ...]:
    boxes: list[YoloBox] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        content = raw_line.strip()
        if not content:
            continue
        parts = content.split()
        if len(parts) != 5:
            raise AnnotationFormatError(path, line_number, content)
        try:
            class_id, center_x, center_y, width, height = (float(part) for part in parts)
            if not class_id.is_integer():
                raise AnnotationFormatError(path, line_number, content)
            boxes.append(
                YoloBox(
                    class_id=int(class_id),
                    center_x=center_x,
                    center_y=center_y,
                    width=width,
                    height=height,
                )
            )
        except (ValueError, ValidationError) as exc:
            raise AnnotationFormatError(path, line_number, content) from exc
    return tuple(boxes)


def select_validation_samples(
    dataset_root: Path,
    policy: SelectionPolicy,
) -> SampleSelection:
    image_dir = dataset_root / "images" / "val"
    label_dir = dataset_root / "labels" / "val"
    candidates: list[DatasetSample] = []
    scanned_images = 0
    rejected = {reason: 0 for reason in RejectionReason}

    for image_path in sorted(image_dir.iterdir(), key=lambda item: item.name.casefold()):
        if image_path.suffix.casefold() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        if image_path.name in policy.excluded_names:
            continue
        label_path = label_dir / f"{image_path.stem}.txt"
        if not label_path.exists():
            continue
        scanned_images += 1
        boxes = parse_yolo_labels(label_path)
        for box in boxes:
            reason = audit_box(box, policy.thresholds)
            if reason is not None:
                rejected[reason] += 1
        compatible = select_compatible_boxes(boxes, policy.thresholds, limit=len(boxes))
        if len(compatible) >= 3:
            candidates.append(DatasetSample(image_path=image_path, label_path=label_path, boxes=compatible))

    selected: list[DatasetSample] = []
    uncovered = set(range(len(CLASS_NAMES)))
    remaining = candidates.copy()
    while remaining and len(selected) < policy.limit:
        remaining.sort(
            key=lambda sample: (
                -len({box.class_id for box in sample.boxes} & uncovered),
                -len({box.class_id for box in sample.boxes}),
                sample.image_path.name.casefold(),
            )
        )
        chosen = remaining.pop(0)
        selected.append(chosen)
        uncovered.difference_update(box.class_id for box in chosen.boxes)

    return SampleSelection(
        samples=tuple(selected),
        audit=DatasetAudit(
            scanned_images=scanned_images,
            eligible_images=len(candidates),
            rejected_clipped=rejected[RejectionReason.CLIPPED],
            rejected_border_touching=rejected[RejectionReason.BORDER_TOUCHING],
            rejected_small_area=rejected[RejectionReason.SMALL_AREA],
            rejected_small_side=rejected[RejectionReason.SMALL_SIDE],
        ),
    )
