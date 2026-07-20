from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Request

from app.config import get_settings


router = APIRouter(tags=["Sensor IoT"])
settings = get_settings()


@router.get("/sensor-status")
async def sensor_status(request: Request) -> dict[str, Any]:
    now_ms = int(time.time() * 1000)
    sensor_bridge = getattr(request.app.state, "sensor_bridge", None)
    if sensor_bridge is None:
        return {
            "success": True,
            "enabled": False,
            "connected": False,
            "port": None,
            "capture_time_ms": now_ms,
            "window_ms": settings.sensor_status_window_ms,
            "status": "disabled",
            "samples": {},
            "reader_error": None,
            "connection_attempts": 0,
            "last_sample_time_ms": None,
        }
    return {
        "success": True,
        **sensor_bridge.snapshot(now_ms, settings.sensor_status_window_ms),
    }
