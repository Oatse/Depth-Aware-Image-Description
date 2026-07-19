from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image

from app.config import Settings
from models.depth_anything import DepthAnything
from prototypes.depth_guided_roi_v3.models import ExperimentConfig, PreparedSample, SampleSelection
from prototypes.depth_guided_roi_v3.selection import (
    filter_depth_stable_boxes,
    select_control_marks,
    select_depth_marks,
)
from prototypes.depth_guided_roi_v3.visuals import (
    depth_visual,
    draw_audit_boxes,
    draw_marks,
    make_contact_sheet,
)


@dataclass(frozen=True, slots=True)
class PreparationError(Exception):
    image_name: str
    reason: str

    def __str__(self) -> str:
        return f"Failed to prepare {self.image_name}: {self.reason}"


def prepare_samples(
    settings: Settings,
    selection: SampleSelection,
    config: ExperimentConfig,
) -> tuple[PreparedSample, ...]:
    output_root = config.paths.output_root
    audit_dir = output_root / "audit_overlays"
    control_dir = output_root / "som_control"
    depth_guided_dir = output_root / "depth_guided"
    depth_map_dir = output_root / "depth_maps"
    for directory in (audit_dir, control_dir, depth_guided_dir, depth_map_dir):
        directory.mkdir(parents=True, exist_ok=True)

    depth_model = DepthAnything(settings.model_copy(update={"save_depth_map": False}))
    prepared: list[PreparedSample] = []
    audit_paths: list[Path] = []
    control_paths: list[Path] = []
    depth_guided_paths: list[Path] = []
    manifest_rows: list[dict[str, str | int | float | None]] = []

    for sample in selection.samples:
        with Image.open(sample.image_path) as opened:
            image = opened.convert("RGB")
        depth_result = depth_model.estimate(image, sample.image_path.name)
        if not depth_result.success or depth_result.depth_map is None:
            raise PreparationError(sample.image_path.name, depth_result.error or "depth estimation failed")

        stable_boxes = filter_depth_stable_boxes(
            depth_result.depth_map,
            sample.boxes,
            config.max_relative_depth_spread,
        )
        control_marks = select_control_marks(stable_boxes, config.marks_per_image)
        depth_marks = select_depth_marks(depth_result.depth_map, stable_boxes, config.marks_per_image)
        if len(control_marks) != config.marks_per_image or len(depth_marks) != config.marks_per_image:
            raise PreparationError(sample.image_path.name, "fewer than the required marks were produced")

        audit_path = audit_dir / f"{sample.image_path.stem}_audit.jpg"
        control_path = control_dir / f"{sample.image_path.stem}_control.jpg"
        depth_guided_path = depth_guided_dir / f"{sample.image_path.stem}_depth_guided.jpg"
        draw_audit_boxes(image, sample.boxes).save(audit_path, quality=92)
        draw_marks(image, control_marks).save(control_path, quality=92)
        draw_marks(image, depth_marks).save(depth_guided_path, quality=92)
        depth_visual(depth_result.depth_map).save(depth_map_dir / f"{sample.image_path.stem}_depth.png")

        audit_paths.append(audit_path)
        control_paths.append(control_path)
        depth_guided_paths.append(depth_guided_path)
        prepared.append(
            PreparedSample(
                sample=sample,
                baseline_path=sample.image_path,
                control_path=control_path,
                depth_guided_path=depth_guided_path,
                control_marks=control_marks,
                depth_marks=depth_marks,
            )
        )
        for mark in depth_marks:
            manifest_rows.append(
                {
                    "image": sample.image_path.name,
                    "mark_id": mark.mark_id,
                    "class_id": mark.box.class_id,
                    "median_depth": mark.median_depth,
                    "p10_depth": mark.p10_depth,
                }
            )

    make_contact_sheet(audit_paths, output_root / "audit_contact_sheet.jpg")
    make_contact_sheet(control_paths, output_root / "control_contact_sheet.jpg")
    make_contact_sheet(depth_guided_paths, output_root / "depth_guided_contact_sheet.jpg")
    (output_root / "selection_manifest.json").write_text(
        json.dumps(
            {
                "protocol": {
                    "image_limit": config.image_limit,
                    "marks_per_image": config.marks_per_image,
                    "dataset_audit": asdict(selection.audit),
                },
                "depth_ranked_marks": manifest_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return tuple(prepared)
