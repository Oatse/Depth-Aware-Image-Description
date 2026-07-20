from fastapi.testclient import TestClient

import app.routes.readiness as readiness_route
from app.main import app


class ReadyGemma:
    async def check_status(self):
        return "ready"


class PairedBridge:
    def snapshot(self, _capture_time_ms, _window_ms):
        return {"status": "paired", "connected": True, "samples": {"sensor_1": {}, "sensor_2": {}}}


def test_readiness_reports_each_gate_without_hiding_missing_calibration(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(readiness_route, "gemma_client", ReadyGemma())
    monkeypatch.setattr(readiness_route.settings, "sensor_calibration_path", tmp_path / "missing.json")
    with TestClient(app) as client:
        app.state.sensor_bridge = PairedBridge()
        response = client.get("/readiness")
    payload = response.json()
    assert response.status_code == 200
    assert payload["checks"]["gemma"] == "ready"
    assert payload["checks"]["sensor"] == "paired"
    assert payload["checks"]["calibration"]["status"] == "missing"
    assert payload["ready"] is False
