import csv
from pathlib import Path

from scripts.run_batch_evaluation import _read_successful_job_keys
from services.result_logger import PREDICTION_FIELDS


def test_read_successful_job_keys_ignores_failed_rows(tmp_path: Path) -> None:
    predictions_path = tmp_path / "predictions.csv"

    with predictions_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREDICTION_FIELDS)
        writer.writeheader()
        writer.writerow({
            "image_name": "indoor_001.webp",
            "mode": "gemma_only",
            "error": "",
        })
        writer.writerow({
            "image_name": "indoor_001.webp",
            "mode": "gemma_depth",
            "error": "Gemma returned an empty description.",
        })

    completed_jobs = _read_successful_job_keys(predictions_path)

    assert completed_jobs == {("indoor_001.webp", "gemma_only")}
