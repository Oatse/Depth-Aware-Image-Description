import json
from pathlib import Path

from fastapi.testclient import TestClient

import app.routes.sensor_calibration as calibration_route
from app.main import app
from services.sensor_calibration import build_calibration_profile


class CalibrationBridge:
    def __init__(self, pairs: list[tuple[float, float]]) -> None:
        self.pairs = iter(enumerate(pairs, start=1))

    def snapshot(self, capture_time_ms: int, window_ms: int) -> dict:
        seq, (sensor_1_cm, sensor_2_cm) = next(self.pairs)
        return {
            "enabled": True,
            "connected": True,
            "status": "paired",
            "capture_time_ms": capture_time_ms,
            "window_ms": window_ms,
            "samples": {
                "sensor_1": {
                    "distance_cm": sensor_1_cm,
                    "age_ms": 10,
                    "status": "ok",
                    "seq": seq,
                    "received_time_ms": capture_time_ms - 10,
                },
                "sensor_2": {
                    "distance_cm": sensor_2_cm,
                    "age_ms": 20,
                    "status": "ok",
                    "seq": seq,
                    "received_time_ms": capture_time_ms - 20,
                },
            },
        }


def _set_paths(monkeypatch, tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    profile_path = tmp_path / "sensor_camera_calibration.json"
    measurements_path = tmp_path / "sensor_camera_calibration_measurements.json"
    verification_path = tmp_path / "sensor_camera_verification.json"
    verification_measurements_path = tmp_path / "sensor_camera_verification_measurements.json"
    monkeypatch.setattr(calibration_route.settings, "sensor_calibration_path", profile_path)
    monkeypatch.setattr(calibration_route.settings, "sensor_calibration_measurements_path", measurements_path)
    monkeypatch.setattr(calibration_route.settings, "sensor_verification_path", verification_path)
    monkeypatch.setattr(
        calibration_route.settings,
        "sensor_verification_measurements_path",
        verification_measurements_path,
    )
    return profile_path, measurements_path, verification_path, verification_measurements_path


def _seed_calibration(measurements_path: Path, samples_at_200: int = 30) -> list[dict]:
    measurements = []
    for reference in (20.0, 60.0, 100.0, 150.0, 200.0):
        count = samples_at_200 if reference == 200 else 30
        for index in range(count):
            sensor_1 = reference - 3.0 + (index % 2) * 0.1
            sensor_2 = reference - 2.0 + (index % 3) * 0.1
            measurements.append(
                {
                    "captured_at_ms": index,
                    "measured_cm": reference,
                    "sensor_1_cm": sensor_1,
                    "sensor_2_cm": sensor_2,
                    "sensor_cm": (sensor_1 + sensor_2) / 2,
                    "residual_cm": abs(reference - (sensor_1 + sensor_2) / 2),
                }
            )
    measurements_path.write_text(json.dumps(measurements), encoding="utf-8")
    return measurements


def test_calibration_api_completes_five_by_thirty_profile_and_freezes_it(monkeypatch, tmp_path) -> None:
    profile_path, measurements_path, _, _ = _set_paths(monkeypatch, tmp_path)
    _seed_calibration(measurements_path, samples_at_200=29)
    bridge = CalibrationBridge([(197.0, 198.0)])

    with TestClient(app) as client:
        app.state.sensor_bridge = bridge
        final_capture = client.post("/sensor-calibration/captures", json={"measured_cm": 200})
        frozen_capture = client.post("/sensor-calibration/captures", json={"measured_cm": 200})
        status_response = client.get("/sensor-calibration")

    assert final_capture.status_code == 200
    assert final_capture.json()["profile"]["validated"] is True
    assert final_capture.json()["profile"]["capture_count"] == 150
    assert frozen_capture.status_code == 409
    assert "dibekukan" in frozen_capture.json()["detail"]
    assert status_response.json()["profile"]["correction_model"]["sensor_1"]["r2"] > 0.999
    assert profile_path.exists()


def test_verification_capture_is_corrected_and_saved_separately(monkeypatch, tmp_path) -> None:
    profile_path, measurements_path, verification_path, verification_measurements_path = _set_paths(monkeypatch, tmp_path)
    calibration_measurements = _seed_calibration(measurements_path)
    profile_path.write_text(json.dumps(build_calibration_profile(calibration_measurements)), encoding="utf-8")
    bridge = CalibrationBridge([(37.0, 38.0)])

    with TestClient(app) as client:
        app.state.sensor_bridge = bridge
        response = client.post("/sensor-calibration/verification/captures", json={"measured_cm": 40})

    assert response.status_code == 200
    measurement = response.json()["measurement"]
    assert measurement["corrected_frontal_cm"] > measurement["raw_frontal_cm"]
    assert json.loads(measurements_path.read_text(encoding="utf-8")) == calibration_measurements
    assert verification_path.exists()
    assert len(json.loads(verification_measurements_path.read_text(encoding="utf-8"))) == 1


def test_verification_rejects_a_calibration_reference_distance(monkeypatch, tmp_path) -> None:
    _, measurements_path, _, verification_measurements_path = _set_paths(monkeypatch, tmp_path)
    _seed_calibration(measurements_path)

    with TestClient(app) as client:
        response = client.post("/sensor-calibration/verification/captures", json={"measured_cm": 60})

    assert response.status_code == 422
    assert not verification_measurements_path.exists()


def test_verification_accepts_upper_holdout_distances(monkeypatch, tmp_path) -> None:
    _, measurements_path, _, verification_measurements_path = _set_paths(monkeypatch, tmp_path)
    _seed_calibration(measurements_path)
    bridge = CalibrationBridge([(122.0, 123.0), (172.0, 173.0)])

    with TestClient(app) as client:
        app.state.sensor_bridge = bridge
        at_125 = client.post("/sensor-calibration/verification/captures", json={"measured_cm": 125})
        at_175 = client.post("/sensor-calibration/verification/captures", json={"measured_cm": 175})

    assert at_125.status_code == 200
    assert at_175.status_code == 200
    saved = json.loads(verification_measurements_path.read_text(encoding="utf-8"))
    assert [item["measured_cm"] for item in saved] == [125.0, 175.0]


def test_verification_rejects_distance_above_operational_scope(monkeypatch, tmp_path) -> None:
    _, measurements_path, _, verification_measurements_path = _set_paths(monkeypatch, tmp_path)
    _seed_calibration(measurements_path)

    with TestClient(app) as client:
        response = client.post("/sensor-calibration/verification/captures", json={"measured_cm": 201})

    assert response.status_code == 422
    assert not verification_measurements_path.exists()


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


def test_calibration_reset_removes_calibration_and_verification_files(monkeypatch, tmp_path) -> None:
    paths = _set_paths(monkeypatch, tmp_path)
    for path in paths:
        path.write_text("[]", encoding="utf-8")

    with TestClient(app) as client:
        response = client.delete("/sensor-calibration")

    assert response.status_code == 200
    assert all(not path.exists() for path in paths)
