from __future__ import annotations

import json

from services.result_logger import log_sensor_evidence


def test_sensor_capture_evidence_is_persisted_as_auditable_jsonl(tmp_path) -> None:
    evidence = {
        "capture_id": "cap_123",
        "client_capture_time_ms": 123,
        "match_time_source": "client_capture",
        "status": "paired",
        "samples": {
            "sensor_1": {"distance_cm": 80.1, "age_ms": -5},
            "sensor_2": {"distance_cm": 82.4, "age_ms": 8},
        },
    }

    log_sensor_evidence(tmp_path, image_name="camera.jpg", mode="sensor_assisted", evidence=evidence)

    lines = (tmp_path / "sensor_captures.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["logged_at"]
    assert record["image_name"] == "camera.jpg"
    assert record["mode"] == "sensor_assisted"
    assert record["sensor_evidence"]["capture_id"] == "cap_123"
    assert record["sensor_evidence"]["samples"]["sensor_2"]["distance_cm"] == 82.4
