import io
import time

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from models.gemma_client import GemmaClientError, GemmaResult


def _sample_image_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (40, 32), color=(150, 160, 120)).save(buffer, format="JPEG")
    return buffer.getvalue()


class FakeGemmaClient:
    def __init__(self, description: str = "Meja terlihat di tengah ruangan.") -> None:
        self.description = description
        self.calls = 0

    async def describe_image(self, base64_image: str, prompt: str | None = None) -> GemmaResult:
        self.calls += 1
        assert base64_image
        return GemmaResult(
            self.description,
            "{}",
            5,
            mock=True,
            structured={
                "scene_type": "indoor",
                "main_object": "meja",
                "object_position": "tengah",
                "objects": ["meja"],
                "obstacle_candidate": "tidak_diketahui",
                "description": self.description,
            },
        )


class SensorBridge:
    def __init__(self, samples: dict, *, status: str = "paired") -> None:
        self.samples = samples
        self.status = status

    def snapshot(self, capture_time_ms: int, window_ms: int) -> dict:
        return {
            "enabled": True,
            "connected": True,
            "capture_time_ms": capture_time_ms,
            "window_ms": window_ms,
            "status": self.status,
            "samples": self.samples,
        }


def _analyze(client: TestClient, **data: str):
    payload = {"save_result": "false", **data}
    return client.post(
        "/analyze",
        files={"image": ("sample.jpg", _sample_image_bytes(), "image/jpeg")},
        data=payload,
    )


def test_health_exposes_only_active_runtime_checks(monkeypatch) -> None:
    import app.main as main_module

    async def ready():
        return "mock"

    monkeypatch.setattr(main_module.gemma_client, "check_status", ready)
    with TestClient(app) as client:
        payload = client.get("/health").json()
    assert payload == {
        "success": True,
        "app": "Indoor Visual-Spatial Description",
        "backend": "ok",
        "gemma": "mock",
        "gemma_model": "google/gemma-4-e2b",
    }


def test_default_sensor_assisted_uses_one_rgb_inference_and_reports_unavailable(monkeypatch) -> None:
    import app.routes.analyze as analyze_route

    fake = FakeGemmaClient()
    monkeypatch.setattr(analyze_route, "gemma_client", fake)
    with TestClient(app) as client:
        response = _analyze(client)
    payload = response.json()
    assert response.status_code == 200
    assert fake.calls == 1
    assert payload["mode"] == "sensor_assisted"
    assert payload["analysis_method"] == "sensor_assisted"
    assert payload["sensor_contribution"]["status"] == "insufficient"
    assert payload["sensor_contribution"]["reason_code"] == "sensor_unavailable"
    assert payload["sensor_contribution"]["frontal_reference_cm"] is None


def test_paired_sensor_uses_arithmetic_mean_without_object_binding(monkeypatch) -> None:
    import app.routes.analyze as analyze_route

    fake = FakeGemmaClient("Meja terlihat di tengah ruangan.")
    monkeypatch.setattr(analyze_route, "gemma_client", fake)
    capture_time = int(time.time() * 1000)
    bridge = SensorBridge({
        "sensor_1": {"distance_cm": 78.0, "age_ms": 4, "status": "ok"},
        "sensor_2": {"distance_cm": 82.0, "age_ms": 6, "status": "ok"},
    })
    with TestClient(app) as client:
        app.state.sensor_bridge = bridge
        response = _analyze(
            client,
            capture_id="cap-paired",
            capture_time_ms=str(capture_time),
            camera_facing_mode="environment",
        )
    payload = response.json()
    contribution = payload["sensor_contribution"]
    assert fake.calls == 1
    assert contribution["status"] == "applied"
    assert contribution["sensor_1_cm"] == 78.0
    assert contribution["sensor_2_cm"] == 82.0
    assert contribution["pair_disagreement_cm"] == 4.0
    sensor_1_corrected = contribution["sensor_1_corrected_cm"]
    sensor_2_corrected = contribution["sensor_2_corrected_cm"]
    corrected_mean = round((sensor_1_corrected + sensor_2_corrected) / 2, 2)
    assert sensor_1_corrected > contribution["sensor_1_cm"]
    assert sensor_2_corrected > contribution["sensor_2_cm"]
    assert contribution["frontal_reference_cm"] == corrected_mean
    assert payload["final_description"].endswith(
        f"Referensi jarak frontal sekitar {corrected_mean:.1f} cm pada arah sensor."
    )
    assert "Meja berjarak" not in payload["final_description"]


def test_conflicting_pair_withholds_numeric_reference_from_final_description(monkeypatch) -> None:
    import app.routes.analyze as analyze_route

    monkeypatch.setattr(analyze_route, "gemma_client", FakeGemmaClient())
    bridge = SensorBridge({
        "sensor_1": {"distance_cm": 40.0, "age_ms": 4, "status": "ok"},
        "sensor_2": {"distance_cm": 90.0, "age_ms": 6, "status": "ok"},
    })
    with TestClient(app) as client:
        app.state.sensor_bridge = bridge
        response = _analyze(
            client,
            capture_time_ms=str(int(time.time() * 1000)),
            camera_facing_mode="environment",
        )
    payload = response.json()
    contribution = payload["sensor_contribution"]
    assert contribution["status"] == "conflict"
    assert contribution["frontal_reference_cm"] is None
    assert contribution["sensor_1_cm"] == 40.0
    assert contribution["sensor_2_cm"] == 90.0
    assert "40.0 cm" not in payload["final_description"]
    assert "90.0 cm" not in payload["final_description"]


def test_partial_sensor_is_labeled_and_never_presented_as_pair_average(monkeypatch) -> None:
    import app.routes.analyze as analyze_route

    monkeypatch.setattr(analyze_route, "gemma_client", FakeGemmaClient())
    bridge = SensorBridge({"sensor_1": {"distance_cm": 55.0, "age_ms": 5, "status": "ok"}}, status="partial")
    with TestClient(app) as client:
        app.state.sensor_bridge = bridge
        response = _analyze(
            client,
            capture_time_ms=str(int(time.time() * 1000)),
            camera_facing_mode="environment",
        )
    contribution = response.json()["sensor_contribution"]
    assert contribution["status"] == "partial"
    assert contribution["frontal_reference_cm"] is None
    assert "Sensor 1 membaca 55.0 cm" in contribution["description"]
    assert "bukan rata-rata" in contribution["description"]


def test_only_two_public_modes_are_accepted(monkeypatch) -> None:
    import app.routes.analyze as analyze_route

    monkeypatch.setattr(analyze_route, "gemma_client", FakeGemmaClient())
    with TestClient(app) as client:
        assert _analyze(client, mode="gemma_only").status_code == 200
        rejected = _analyze(client, mode="legacy_mode")
    assert rejected.status_code == 400
    assert "gemma_only, sensor_assisted" in rejected.json()["error"]


def test_gemma_only_system_note_matches_default_visual_prompt(monkeypatch) -> None:
    import app.routes.analyze as analyze_route

    monkeypatch.setattr(analyze_route, "gemma_client", FakeGemmaClient())
    with TestClient(app) as client:
        response = _analyze(client, mode="gemma_only")

    payload = response.json()
    assert payload["display"]["sensor_contribution"] is None
    assert payload["display"]["system_note"] == (
        "Gemma menggunakan prompt visual default tanpa konteks sensor."
    )


def test_analysis_job_completes_with_sensor_assisted_default(monkeypatch) -> None:
    import app.routes.analyze as analyze_route

    monkeypatch.setattr(analyze_route, "gemma_client", FakeGemmaClient())
    with TestClient(app) as client:
        accepted = client.post(
            "/analysis-jobs",
            files={"image": ("sample.jpg", _sample_image_bytes(), "image/jpeg")},
            data={"save_result": "false"},
        )
        result = None
        for _ in range(100):
            result = client.get(accepted.json()["poll_url"]).json()
            if result["status"] in {"completed", "failed"}:
                break
            time.sleep(0.01)
    assert accepted.status_code == 202
    assert result is not None
    assert result["status"] == "completed"
    assert result["result"]["mode"] == "sensor_assisted"


def test_gemma_failure_is_reported(monkeypatch) -> None:
    import app.routes.analyze as analyze_route

    class FailingGemma:
        async def describe_image(self, _base64_image: str, prompt: str | None = None):
            raise GemmaClientError("Gemma gagal menghasilkan deskripsi.")

    monkeypatch.setattr(analyze_route, "gemma_client", FailingGemma())
    with TestClient(app) as client:
        response = _analyze(client, mode="gemma_only")
    assert response.status_code == 502
    assert "Gemma gagal" in response.json()["error"]


def test_retired_comparison_route_is_not_exposed() -> None:
    with TestClient(app) as client:
        assert client.post("/analysis-comparisons").status_code == 404
