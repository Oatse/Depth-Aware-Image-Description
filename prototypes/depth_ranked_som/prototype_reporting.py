from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Final

from rich.console import Console
from rich.table import Table

from prototypes.depth_ranked_som.prototype_models import (
    CLASS_NAMES,
    CheckpointState,
    ImageState,
    PrototypeSummary,
    PrototypeTotals,
)


REQUIRED_IMAGE_COVERAGE: Final = 1.0
REQUIRED_MARK_COVERAGE: Final = 0.9
REQUIRED_OBJECT_ACCURACY: Final = 0.7


def build_summary(totals: PrototypeTotals) -> PrototypeSummary:
    image_coverage = totals.completed_images / totals.selected_images if totals.selected_images else 0.0
    mark_coverage = totals.returned_marks / totals.expected_marks if totals.expected_marks else 0.0
    object_accuracy = totals.matched_marks / totals.expected_marks if totals.expected_marks else 0.0
    mean_latency = sum(totals.latencies) / len(totals.latencies) if totals.latencies else 0.0
    gate_passed = (
        image_coverage >= REQUIRED_IMAGE_COVERAGE
        and mark_coverage >= REQUIRED_MARK_COVERAGE
        and object_accuracy >= REQUIRED_OBJECT_ACCURACY
        and totals.hallucinated_mark_ids == 0
    )
    gate_reason = (
        "PASS: SoM oracle-box layak dilanjutkan ke audit depth ranking."
        if gate_passed
        else "FAIL: jangan melatih detector; perbaiki atau buang mekanisme mark terlebih dahulu."
    )
    return PrototypeSummary(
        selected_images=totals.selected_images,
        completed_images=totals.completed_images,
        expected_marks=totals.expected_marks,
        returned_marks=totals.returned_marks,
        matched_marks=totals.matched_marks,
        hallucinated_mark_ids=totals.hallucinated_mark_ids,
        image_coverage=round(image_coverage, 4),
        mark_coverage=round(mark_coverage, 4),
        object_accuracy=round(object_accuracy, 4),
        mean_gemma_latency_ms=round(mean_latency, 2),
        gate_passed=gate_passed,
        gate_reason=gate_reason,
    )


def write_image_error(response_dir: Path, image_name: str, error: str) -> None:
    (response_dir / f"{Path(image_name).stem}_error.json").write_text(
        json.dumps({"image": image_name, "error": error}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_checkpoint(output_root: Path, state: CheckpointState) -> None:
    (output_root / "checkpoint.json").write_text(
        json.dumps(asdict(state), indent=2),
        encoding="utf-8",
    )


def print_image_state(state: ImageState) -> None:
    table = Table(title=f"[{state.index}/{state.total}] {state.image_name}")
    table.add_column("Mark")
    table.add_column("Expected")
    table.add_column("Predicted")
    table.add_column("Median depth")
    for mark in state.marks:
        table.add_row(
            str(mark.mark_id),
            CLASS_NAMES[mark.box.class_id],
            state.answers.get(mark.mark_id, "missing"),
            f"{mark.median_depth:.3f}",
        )
    Console().print(table)
