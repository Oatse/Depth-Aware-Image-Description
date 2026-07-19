#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "anyio",
#     "httpx",
#     "numpy",
#     "onnxruntime",
#     "pillow",
#     "pydantic",
#     "pydantic-settings",
#     "rich",
#     "typer",
# ]
# ///

# ------------------ How to run ------------------
# From Program/: python prototypes/depth_ranked_som/run_oracle_som_prototype.py
# Optional: --dataset-root "D:/Tugas/DUMP/homeobjects-3K" --limit 12
# This prototype uses the existing local model configuration and does not train a detector.
# ------------------------------------------------

from __future__ import annotations

import csv
import json
import sys
from dataclasses import asdict, fields
from pathlib import Path
from typing import Final

import anyio
import typer
from PIL import Image
from pydantic import ValidationError
from rich.console import Console


PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from models.depth_anything import DepthAnything
from models.gemma_client import GemmaClient, GemmaClientError
from prototypes.depth_ranked_som.oracle_som_logic import (
    CLASS_NAMES,
    build_mark_prompt,
    depth_visual,
    draw_marks,
    make_contact_sheet,
    prediction_matches,
    rank_boxes_by_depth,
    select_validation_samples,
)
from prototypes.depth_ranked_som.prototype_models import (
    CheckpointState,
    ImageState,
    MarkResponse,
    MarkResultRow,
    PrototypeRuntimeError,
    PrototypeSummary,
    PrototypeTotals,
)
from prototypes.depth_ranked_som.prototype_reporting import (
    build_summary,
    print_image_state,
    write_checkpoint,
    write_image_error,
)
from services.image_preprocess import preprocess_image


DEFAULT_DATASET_ROOT: Final = Path("D:/Tugas/DUMP/homeobjects-3K")
DEFAULT_OUTPUT_ROOT: Final = PROJECT_ROOT / "results" / "prototypes" / "depth_ranked_som_20260714"
async def run_prototype(dataset_root: Path, output_root: Path, limit: int) -> PrototypeSummary:
    settings = get_settings().model_copy(update={"save_depth_map": False})
    gemma_client = GemmaClient(settings)
    gemma_status = await gemma_client.check_status()
    if gemma_status != "ready":
        raise PrototypeRuntimeError(f"Gemma is not ready: {gemma_status}")

    samples = select_validation_samples(dataset_root, limit)
    if len(samples) != limit:
        raise PrototypeRuntimeError(f"Only {len(samples)} eligible validation images were found; expected {limit}.")

    output_root.mkdir(parents=True, exist_ok=True)
    marked_dir = output_root / "marked"
    depth_dir = output_root / "depth"
    response_dir = output_root / "responses"
    for directory in (marked_dir, depth_dir, response_dir):
        directory.mkdir(parents=True, exist_ok=True)

    depth_model = DepthAnything(settings)
    rows: list[MarkResultRow] = []
    completed_images = 0
    returned_marks = 0
    expected_marks = 0
    matched_marks = 0
    hallucinated_mark_ids = 0
    latencies: list[int] = []
    marked_paths: list[Path] = []

    csv_path = output_root / "mark_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csv_handle:
        writer = csv.DictWriter(csv_handle, fieldnames=[field.name for field in fields(MarkResultRow)])
        writer.writeheader()

        for index, sample in enumerate(samples, start=1):
            with Image.open(sample.image_path) as opened:
                image = opened.convert("RGB")
            depth_result = depth_model.estimate(image, sample.image_path.name)
            if not depth_result.success or depth_result.depth_map is None:
                write_image_error(response_dir, sample.image_path.name, depth_result.error or "depth failed")
                write_checkpoint(output_root, CheckpointState(index, limit, len(rows)))
                continue

            marks = rank_boxes_by_depth(depth_result.depth_map, sample.boxes)
            if not marks:
                write_image_error(response_dir, sample.image_path.name, "no finite depth inside oracle boxes")
                write_checkpoint(output_root, CheckpointState(index, limit, len(rows)))
                continue

            expected_ids = {mark.mark_id for mark in marks}
            expected_marks += len(marks)
            marked_image = draw_marks(image, marks)
            marked_path = marked_dir / f"{sample.image_path.stem}_marked.jpg"
            marked_image.save(marked_path, quality=92)
            marked_paths.append(marked_path)
            depth_visual(depth_result.depth_map).save(depth_dir / f"{sample.image_path.stem}_depth.png")

            processed = preprocess_image(marked_path.read_bytes(), settings.image_max_dimension)
            try:
                gemma_result = await gemma_client.describe_image(
                    processed.base64_image,
                    prompt=build_mark_prompt(sorted(expected_ids)),
                )
            except GemmaClientError as exc:
                write_image_error(response_dir, sample.image_path.name, str(exc))
                write_checkpoint(output_root, CheckpointState(index, limit, len(rows)))
                continue
            try:
                response = MarkResponse.model_validate(gemma_result.structured)
            except ValidationError as exc:
                (response_dir / f"{sample.image_path.stem}_invalid_response.json").write_text(
                    json.dumps(
                        {
                            "image": sample.image_path.name,
                            "error": str(exc),
                            "parsed_response": gemma_result.structured,
                            "raw_response": gemma_result.raw_response,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                write_checkpoint(output_root, CheckpointState(index, limit, len(rows)))
                continue

            answer_by_id = {answer.mark_id: answer.object_name for answer in response.marks}
            returned_ids = set(answer_by_id) & expected_ids
            returned_marks += len(returned_ids)
            hallucinated_mark_ids += len(set(answer_by_id) - expected_ids)
            latencies.append(gemma_result.latency_ms)
            completed_images += 1

            for mark in marks:
                predicted = answer_by_id.get(mark.mark_id, "tidak_dikembalikan")
                is_match = prediction_matches(mark.box.class_id, predicted)
                matched_marks += int(is_match)
                row = MarkResultRow(
                    image_name=sample.image_path.name,
                    mark_id=mark.mark_id,
                    expected_class=CLASS_NAMES[mark.box.class_id],
                    predicted_object=predicted,
                    object_match=is_match,
                    median_depth=round(mark.median_depth, 4),
                    p10_depth=round(mark.p10_depth, 4),
                    gemma_latency_ms=gemma_result.latency_ms,
                    audit_status="parsed" if mark.mark_id in returned_ids else "missing_mark",
                )
                rows.append(row)
                writer.writerow(asdict(row))
            csv_handle.flush()

            (response_dir / f"{sample.image_path.stem}.json").write_text(
                json.dumps(
                    {
                        "image": sample.image_path.name,
                        "expected": [
                            {
                                "id": mark.mark_id,
                                "class": CLASS_NAMES[mark.box.class_id],
                                "median_depth": mark.median_depth,
                                "p10_depth": mark.p10_depth,
                            }
                            for mark in marks
                        ],
                        "parsed_response": response.model_dump(by_alias=True),
                        "raw_response": gemma_result.raw_response,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            write_checkpoint(output_root, CheckpointState(index, limit, len(rows)))
            print_image_state(ImageState(index, limit, sample.image_path.name, marks, answer_by_id))

    summary = build_summary(
        PrototypeTotals(
            selected_images=len(samples),
            completed_images=completed_images,
            expected_marks=expected_marks,
            returned_marks=returned_marks,
            matched_marks=matched_marks,
            hallucinated_mark_ids=hallucinated_mark_ids,
            latencies=tuple(latencies),
        )
    )
    (output_root / "summary.json").write_text(
        json.dumps(asdict(summary), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    make_contact_sheet(marked_paths, output_root / "marked_contact_sheet.jpg")
    make_contact_sheet(sorted(depth_dir.glob("*.png")), output_root / "depth_contact_sheet.jpg")
    return summary


def main(
    dataset_root: Path = typer.Option(DEFAULT_DATASET_ROOT, exists=True, file_okay=False),
    output_root: Path = typer.Option(DEFAULT_OUTPUT_ROOT, file_okay=False),
    limit: int = typer.Option(12, min=1, max=20),
) -> None:
    summary = anyio.run(run_prototype, dataset_root, output_root, limit)
    Console().print_json(json.dumps(asdict(summary), ensure_ascii=False))


if __name__ == "__main__":
    typer.run(main)
