import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from services.run_repository import RunRepository


PREDICTION_FIELDS = [
    "timestamp",
    "image_name",
    "mode",
    "description_gemma",
    "main_object",
    "object_position",
    "scene_type",
    "nearest_region",
    "distance_category",
    "estimated_distance",
    "safe_direction",
    "fusion_policy",
    "final_description",
    "gemma_latency_ms",
    "depth_latency_ms",
    "total_latency_ms",
    "error",
]


def log_prediction(results_dir: Path, row: dict[str, Any]) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "predictions.csv"
    _ensure_prediction_file_schema(output_path)
    with output_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREDICTION_FIELDS)
        writer.writerow({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **{field: row.get(field, "") for field in PREDICTION_FIELDS if field != "timestamp"},
        })


def log_sensor_evidence(
    results_dir: Path,
    *,
    image_name: str,
    mode: str,
    evidence: dict[str, Any],
) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "image_name": image_name,
        "mode": mode,
        "sensor_evidence": evidence,
    }
    with (results_dir / "sensor_captures.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def log_analysis_run(
    results_dir: Path,
    *,
    capture_id: str | None,
    filename: str,
    sensor_evidence: dict[str, Any] | None,
    outputs: dict[str, Any],
    analysis_run_id: str | None = None,
) -> str:
    run_id = analysis_run_id or uuid4().hex
    record = {
        "analysis_run_id": run_id,
        "capture_id": capture_id,
        "image": {"filename": filename},
        "sensor_evidence": sensor_evidence,
        "outputs": outputs,
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    return RunRepository(results_dir / "analysis_runs.jsonl").append(record)


def _ensure_prediction_file_schema(output_path: Path) -> None:
    if not output_path.exists() or output_path.stat().st_size == 0:
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=PREDICTION_FIELDS).writeheader()
        return

    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if reader.fieldnames == PREDICTION_FIELDS:
            return

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREDICTION_FIELDS)
        writer.writeheader()
        for existing_row in rows:
            writer.writerow({field: existing_row.get(field, "") for field in PREDICTION_FIELDS})
