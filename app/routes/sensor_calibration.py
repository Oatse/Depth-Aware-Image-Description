from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.config import get_settings
from services.sensor_calibration import build_calibration_profile, load_measurements, write_json


router = APIRouter(tags=["Sensor IoT"])
settings = get_settings()


class CalibrationCaptureRequest(BaseModel):
    measured_cm: float = Field(gt=5, le=400)


@router.get("/sensor-calibration")
async def sensor_calibration_status() -> dict[str, Any]:
    measurements = load_measurements(settings.sensor_calibration_measurements_path)
    profile = build_calibration_profile(measurements)
    if settings.sensor_calibration_path.exists():
        profile = _load_profile()
    return {"success": True, "profile": profile, "measurements": measurements}


@router.post("/sensor-calibration/captures")
async def capture_sensor_calibration(payload: CalibrationCaptureRequest, request: Request) -> dict[str, Any]:
    sensor_bridge = getattr(request.app.state, "sensor_bridge", None)
    if sensor_bridge is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sensor bridge tidak tersedia.")
    snapshot = sensor_bridge.snapshot(int(time.time() * 1000), settings.sensor_status_window_ms)
    if snapshot.get("status") != "paired":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dua sensor harus paired dan segar.")
    samples = snapshot.get("samples") or {}
    try:
        sensor_1_cm = float(samples["sensor_1"]["distance_cm"])
        sensor_2_cm = float(samples["sensor_2"]["distance_cm"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bacaan dua sensor tidak lengkap.") from exc
    sensor_cm = round((sensor_1_cm + sensor_2_cm) / 2, 3)
    measurement = {
        "captured_at_ms": int(time.time() * 1000),
        "measured_cm": round(payload.measured_cm, 3),
        "sensor_1_cm": round(sensor_1_cm, 3),
        "sensor_2_cm": round(sensor_2_cm, 3),
        "sensor_cm": sensor_cm,
        "residual_cm": round(abs(payload.measured_cm - sensor_cm), 3),
    }
    measurements = load_measurements(settings.sensor_calibration_measurements_path)
    measurements.append(measurement)
    profile = build_calibration_profile(measurements)
    write_json(settings.sensor_calibration_measurements_path, measurements)
    write_json(settings.sensor_calibration_path, profile)
    return {"success": True, "measurement": measurement, "profile": profile, "measurements": measurements}


@router.delete("/sensor-calibration")
async def reset_sensor_calibration() -> dict[str, Any]:
    removed = []
    for path in (settings.sensor_calibration_measurements_path, settings.sensor_calibration_path):
        if path.exists():
            path.unlink()
            removed.append(path.name)
    return {"success": True, "removed": removed}


def _load_profile() -> dict[str, Any]:
    import json

    return json.loads(settings.sensor_calibration_path.read_text(encoding="utf-8"))
