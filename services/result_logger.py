import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
    "final_description",
    "gemma_latency_ms",
    "depth_latency_ms",
    "total_latency_ms",
    "error",
]


def log_prediction(results_dir: Path, row: dict[str, Any]) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "predictions.csv"
    file_exists = output_path.exists()
    with output_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREDICTION_FIELDS)
        if not file_exists or output_path.stat().st_size == 0:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **{field: row.get(field, "") for field in PREDICTION_FIELDS if field != "timestamp"},
        })
