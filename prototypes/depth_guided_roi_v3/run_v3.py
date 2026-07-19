#!/usr/bin/env -S python

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import anyio
import typer
from rich.console import Console


PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from prototypes.depth_guided_roi_v3.dataset import SelectionPolicy, select_validation_samples
from prototypes.depth_guided_roi_v3.evaluation import EvaluationContext, evaluate_prepared
from prototypes.depth_guided_roi_v3.geometry_qa import QaThresholds
from prototypes.depth_guided_roi_v3.inference import check_model_ready
from prototypes.depth_guided_roi_v3.models import ExperimentConfig, ExperimentPaths
from prototypes.depth_guided_roi_v3.preparation import prepare_samples
from prototypes.depth_guided_roi_v3.reporting import write_report


DEFAULT_DATASET_ROOT: Final = Path("D:/Tugas/DUMP/homeobjects-3K")
DEFAULT_OUTPUT_ROOT: Final = PROJECT_ROOT / "results" / "prototypes" / "depth_guided_roi_v3_20260715"
QA_THRESHOLDS: Final = QaThresholds(
    min_area=0.015,
    min_side=0.06,
    max_iou=0.15,
    min_border_margin=0.01,
)
MAX_RELATIVE_DEPTH_SPREAD: Final = 0.5
PREINFERENCE_EXCLUSIONS: Final = frozenset(
    {
        "living_room_1p (143).jpg",
        "living_room_1059.jpg",
    }
)


@dataclass(frozen=True, slots=True)
class ExperimentRuntimeError(Exception):
    reason: str

    def __str__(self) -> str:
        return self.reason


async def run_experiment(config: ExperimentConfig, prepare_only: bool) -> None:
    settings = get_settings().model_copy(update={"save_depth_map": False})
    selection = select_validation_samples(
        config.paths.dataset_root,
        SelectionPolicy(
            limit=config.image_limit,
            thresholds=QA_THRESHOLDS,
            excluded_names=PREINFERENCE_EXCLUSIONS,
        ),
    )
    if len(selection.samples) != config.image_limit:
        raise ExperimentRuntimeError(
            f"Only {len(selection.samples)} geometry-QA samples were selected; expected {config.image_limit}."
        )
    config.paths.output_root.mkdir(parents=True, exist_ok=True)
    (config.paths.output_root / "frozen_protocol.json").write_text(
        json.dumps(
            {
                "conditions": ["baseline", "som_control", "depth_guided"],
                "image_limit": config.image_limit,
                "marks_per_image": config.marks_per_image,
                "qa_thresholds": {
                    "min_area": QA_THRESHOLDS.min_area,
                    "min_side": QA_THRESHOLDS.min_side,
                    "max_iou": QA_THRESHOLDS.max_iou,
                    "min_border_margin": QA_THRESHOLDS.min_border_margin,
                },
                "marked_gate": {
                    "structured_output_compliance": 1.0,
                    "mark_protocol_compliance": 1.0,
                    "target_coverage": 0.9,
                    "end_to_end_accuracy": 0.7,
                    "hallucinated_mark_ids": 0,
                },
                "depth_ground_truth_available": False,
                "detector_training_in_scope": False,
                "max_relative_depth_spread": config.max_relative_depth_spread,
                "preinference_visual_exclusions": {
                    "living_room_1p (143).jpg": "non-photorealistic illustration outside the target camera-image domain",
                    "living_room_1059.jpg": "reserved calibration image; coarse sofa label visually corresponds to an armchair"
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    prepared = prepare_samples(settings, selection, config)
    Console().print(f"Prepared {len(prepared)} images at {config.paths.output_root}")
    if prepare_only:
        return
    if not await check_model_ready(settings):
        raise ExperimentRuntimeError("LM Studio model endpoint is not ready.")
    bundle = await evaluate_prepared(EvaluationContext(settings=settings, config=config), prepared)
    verdict = write_report(config.paths.output_root, bundle)
    Console().print_json(json.dumps(verdict, ensure_ascii=False))


def main(
    dataset_root: Path = typer.Option(DEFAULT_DATASET_ROOT, exists=True, file_okay=False),
    output_root: Path = typer.Option(DEFAULT_OUTPUT_ROOT, file_okay=False),
    limit: int = typer.Option(12, min=1, max=20),
    marks_per_image: int = typer.Option(3, min=1, max=3),
    prepare_only: bool = typer.Option(False),
) -> None:
    config = ExperimentConfig(
        paths=ExperimentPaths(dataset_root=dataset_root, output_root=output_root),
        image_limit=limit,
        marks_per_image=marks_per_image,
        max_relative_depth_spread=MAX_RELATIVE_DEPTH_SPREAD,
    )
    anyio.run(run_experiment, config, prepare_only)


if __name__ == "__main__":
    typer.run(main)
