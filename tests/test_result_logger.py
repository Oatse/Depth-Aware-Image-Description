import csv

from services.result_logger import PREDICTION_FIELDS, log_prediction


def test_prediction_logger_writes_active_sensor_contract(tmp_path) -> None:
    log_prediction(
        tmp_path,
        {
            "image_name": "sample.jpg",
            "mode": "sensor_assisted",
            "analysis_method": "sensor_assisted",
            "description_gemma": "Terlihat meja.",
            "main_object": "meja",
            "sensor_status": "applied",
            "sensor_1_cm": 78.0,
            "sensor_2_cm": 82.0,
            "sensor_pair_disagreement_cm": 4.0,
            "frontal_reference_cm": 80.0,
            "final_description": "Terlihat meja. Referensi jarak frontal sekitar 80.0 cm.",
            "gemma_latency_ms": 12,
            "sensor_latency_ms": 1,
            "total_latency_ms": 13,
        },
    )
    with (tmp_path / "predictions.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["mode"] == "sensor_assisted"
    assert rows[0]["frontal_reference_cm"] == "80.0"
    assert rows[0]["sensor_1_cm"] == "78.0"
    assert rows[0]["sensor_2_cm"] == "82.0"
    assert set(rows[0]) == set(PREDICTION_FIELDS)


def test_prediction_logger_migrates_previous_header_without_losing_rows(tmp_path) -> None:
    path = tmp_path / "predictions.csv"
    path.write_text("timestamp,image_name,mode,final_description\nold,sample.jpg,gemma_only,Terlihat meja.\n", encoding="utf-8")
    log_prediction(tmp_path, {"image_name": "new.jpg", "mode": "gemma_only"})
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert rows[0]["image_name"] == "sample.jpg"
    assert rows[1]["image_name"] == "new.jpg"
