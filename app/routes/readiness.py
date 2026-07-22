import time

from fastapi import APIRouter, Request

from app.config import get_settings
from models.gemma_client import GemmaClient
from services.sensor_calibration import CalibrationProfile

router = APIRouter()
settings = get_settings()
gemma_client = GemmaClient(settings)


@router.get("/readiness")
async def readiness(request: Request) -> dict[str, object]:
    gemma_status = await gemma_client.check_status()
    bridge = getattr(request.app.state, "sensor_bridge", None)
    sensor = bridge.snapshot(int(time.time() * 1000), settings.sensor_status_window_ms) if bridge else {"status": "unavailable", "connected": False}
    calibration = {"status": "missing", "validated": False, "version": None}
    if settings.sensor_calibration_path.exists():
        profile = CalibrationProfile.load(settings.sensor_calibration_path)
        calibration = {"status": profile.status, "validated": profile.validated, "version": profile.version}
    host = request.url.hostname or ""
    secure_context = request.url.scheme == "https" or host in {"localhost", "127.0.0.1", "testserver"}
    checks = {
        "backend": "ready",
        "gemma": gemma_status,
        "gemma_model": settings.lm_studio_model,
        "sensor": sensor.get("status", "unavailable"),
        "two_sensor_fresh": sensor.get("status") == "paired",
        "calibration": calibration,
        "secure_context": secure_context,
    }
    ready_for_analysis = gemma_status in {"ready", "mock"} and secure_context
    return {"ready": ready_for_analysis, "checks": checks}
