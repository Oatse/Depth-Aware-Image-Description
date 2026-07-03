import csv
from pathlib import Path

from services.result_logger import PREDICTION_FIELDS, log_prediction


def test_log_prediction_writes_current_header(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"

    log_prediction(
        results_dir,
        {
            "image_name": "sample.jpg",
            "mode": "gemma_depth",
            "main_object": "kursi",
            "object_position": "tengah",
            "scene_type": "indoor",
            "nearest_region": "lower_center",
            "distance_category": "dekat",
            "estimated_distance": "sekitar 0.5 sampai 1 meter",
            "final_description": "Terlihat kursi di tengah ruangan.",
            "gemma_latency_ms": 10,
            "depth_latency_ms": 20,
            "total_latency_ms": 35,
        },
    )

    output_path = results_dir / "predictions.csv"
    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert reader.fieldnames == PREDICTION_FIELDS
    assert rows[0]["main_object"] == "kursi"
    assert rows[0]["nearest_region"] == "lower_center"


def test_log_prediction_repairs_stale_header(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    output_path = results_dir / "predictions.csv"
    output_path.write_text(
        "timestamp,image_name,mode,description_gemma,nearest_region,distance_category,"
        "estimated_distance,final_description,gemma_latency_ms,depth_latency_ms,total_latency_ms,error\n",
        encoding="utf-8",
    )

    log_prediction(
        results_dir,
        {
            "image_name": "sample.jpg",
            "mode": "gemma_depth",
            "main_object": "kursi",
            "object_position": "tengah",
            "scene_type": "indoor",
        },
    )

    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert reader.fieldnames == PREDICTION_FIELDS
    assert rows[0]["main_object"] == "kursi"
    assert rows[0]["object_position"] == "tengah"
