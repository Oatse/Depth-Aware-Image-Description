from pathlib import Path

from fastapi.testclient import TestClient

import app.routes.sensor_calibration as calibration_route
from app.main import app


class CalibrationBridge:
    def __init__(self, pairs: list[tuple[float, float]]) -> None:
        self.pairs = iter(pairs)

    def snapshot(self, capture_time_ms: int, window_ms: int) -> dict:
        sensor_1_cm, sensor_2_cm = next(self.pairs)
        return {
            "enabled": True,
            "connected": True,
            "status": "paired",
            "capture_time_ms": capture_time_ms,
            "window_ms": window_ms,
            "samples": {
                "sensor_1": {"distance_cm": sensor_1_cm, "age_ms": 10, "status": "ok"},
                "sensor_2": {"distance_cm": sensor_2_cm, "age_ms": 20, "status": "ok"},
            },
        }


def _set_paths(monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    profile_path = tmp_path / "sensor_camera_calibration.json"
    measurements_path = tmp_path / "sensor_camera_calibration_measurements.json"
    monkeypatch.setattr(calibration_route.settings, "sensor_calibration_path", profile_path)
    monkeypatch.setattr(calibration_route.settings, "sensor_calibration_measurements_path", measurements_path)
    return profile_path, measurements_path


def test_calibration_api_builds_valid_profile_from_three_real_reference_points(monkeypatch, tmp_path) -> None:
    profile_path, measurements_path = _set_paths(monkeypatch, tmp_path)
    bridge = CalibrationBridge([(30.5, 31.0), (59.0, 60.0), (90.5, 91.0)])

    with TestClient(app) as client:
        app.state.sensor_bridge = bridge
        first = client.post("/sensor-calibration/captures", json={"measured_cm": 30})
        second = client.post("/sensor-calibration/captures", json={"measured_cm": 60})
        third = client.post("/sensor-calibration/captures", json={"measured_cm": 90})
        status_response = client.get("/sensor-calibration")

    assert first.status_code == 200
    assert first.json()["profile"]["status"] == "insufficient_captures"
    assert second.json()["profile"]["capture_count"] == 2
    assert third.json()["profile"]["validated"] is True
    assert status_response.json()["profile"]["measurement_kind"] == "frontal_planar_distance"
    assert profile_path.exists()
    assert measurements_path.exists()


def test_calibration_api_rejects_unpaired_sensor(monkeypatch, tmp_path) -> None:
    _set_paths(monkeypatch, tmp_path)

    class UnpairedBridge:
        def snapshot(self, capture_time_ms: int, window_ms: int) -> dict:
            return {"status": "partial", "samples": {}}

    with TestClient(app) as client:
        app.state.sensor_bridge = UnpairedBridge()
        response = client.post("/sensor-calibration/captures", json={"measured_cm": 60})

    assert response.status_code == 409
    assert response.json()["detail"] == "Dua sensor harus paired dan segar."


def test_calibration_api_reset_removes_local_profile(monkeypatch, tmp_path) -> None:
    profile_path, measurements_path = _set_paths(monkeypatch, tmp_path)
    profile_path.write_text("{}", encoding="utf-8")
    measurements_path.write_text("[]", encoding="utf-8")

    with TestClient(app) as client:
        response = client.delete("/sensor-calibration")

    assert response.status_code == 200
    assert not profile_path.exists()
    assert not measurements_path.exists()
