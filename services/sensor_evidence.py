from __future__ import annotations

import time
from typing import Any, Protocol


class SensorSnapshotSource(Protocol):
    def snapshot(self, capture_time_ms: int, window_ms: int) -> dict[str, Any]: ...


def collect_sensor_evidence(
    sensor_bridge: SensorSnapshotSource,
    *,
    capture_id: str | None,
    client_capture_time_ms: int | None,
    camera_facing_mode: str | None,
    match_window_ms: int,
    max_clock_skew_ms: int,
    now_ms: int | None = None,
) -> dict[str, Any] | None:
    if client_capture_time_ms is None:
        return None

    host_receive_time_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    capture_transport_delay_ms = host_receive_time_ms - client_capture_time_ms
    clock_skew_exceeded = abs(capture_transport_delay_ms) > max_clock_skew_ms
    match_time_ms = host_receive_time_ms if clock_skew_exceeded else client_capture_time_ms
    match_time_source = "host_receive_fallback" if clock_skew_exceeded else "client_capture"
    if camera_facing_mode == "user":
        evidence: dict[str, Any] = {
            "enabled": False,
            "connected": False,
            "status": "camera_sensor_direction_mismatch",
            "samples": {},
        }
    else:
        evidence = sensor_bridge.snapshot(match_time_ms, match_window_ms)
    evidence.update(
        {
            "capture_id": capture_id,
            "client_capture_time_ms": client_capture_time_ms,
            "host_receive_time_ms": host_receive_time_ms,
            "capture_transport_delay_ms": capture_transport_delay_ms,
            "match_time_ms": match_time_ms,
            "match_time_source": match_time_source,
            "clock_skew_exceeded": clock_skew_exceeded,
            "camera_facing_mode": camera_facing_mode,
        }
    )
    return evidence
