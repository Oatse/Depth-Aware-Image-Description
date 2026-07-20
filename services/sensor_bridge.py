from __future__ import annotations

import json
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SensorSample:
    sensor_id: str
    received_time_ms: int
    device_timestamp_ms: int | None
    distance_cm: float | None
    valid: bool
    status: str
    seq: int | None


class SensorBridge:
    def __init__(
        self,
        port: str | None,
        baud_rate: int,
        buffer_size: int = 512,
        *,
        serial_factory: Callable[..., Any] | None = None,
        reconnect_interval_seconds: float = 1.0,
    ) -> None:
        self.port = port or ""
        self.baud_rate = baud_rate
        self._serial_factory = serial_factory
        self._reconnect_interval_seconds = reconnect_interval_seconds
        self._samples: deque[SensorSample] = deque(maxlen=buffer_size)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_error: str | None = None
        self._connected = False
        self._connection_attempts = 0
        self._last_sample_time_ms: int | None = None
        self._started = False

    @property
    def enabled(self) -> bool:
        return bool(self.port)

    def start(self) -> None:
        if not self.enabled or self._started:
            return
        self._started = True
        self._thread = threading.Thread(target=self._run, name="sensor-serial-reader", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def snapshot(self, capture_time_ms: int, window_ms: int) -> dict[str, Any]:
        with self._lock:
            candidates = list(self._samples)
            last_error = self._last_error
            connected = self._connected
            connection_attempts = self._connection_attempts
            last_sample_time_ms = self._last_sample_time_ms
        evidence: dict[str, Any] = {
            "enabled": self.enabled,
            "port": self.port or None,
            "capture_time_ms": capture_time_ms,
            "window_ms": window_ms,
            "status": "disabled" if not self.enabled else "unavailable",
            "samples": {},
            "reader_error": last_error,
            "connected": connected,
            "connection_attempts": connection_attempts,
            "last_sample_time_ms": last_sample_time_ms,
        }
        if not self.enabled:
            return evidence
        for sensor_id in ("sensor_1", "sensor_2"):
            valid = [
                item
                for item in candidates
                if item.sensor_id == sensor_id
                and item.valid
                and item.distance_cm is not None
                and abs(item.received_time_ms - capture_time_ms) <= window_ms
            ]
            if not valid:
                continue
            selected = min(valid, key=lambda item: abs(item.received_time_ms - capture_time_ms))
            evidence["samples"][sensor_id] = {
                "distance_cm": selected.distance_cm,
                "received_time_ms": selected.received_time_ms,
                "age_ms": capture_time_ms - selected.received_time_ms,
                "device_timestamp_ms": selected.device_timestamp_ms,
                "seq": selected.seq,
                "status": selected.status,
            }
        if len(evidence["samples"]) == 2:
            distances = [value["distance_cm"] for value in evidence["samples"].values()]
            evidence["status"] = "paired"
            evidence["pair_disagreement_cm"] = round(abs(distances[0] - distances[1]), 2)
        elif evidence["samples"]:
            evidence["status"] = "partial"
        return evidence

    def _run(self) -> None:
        serial_factory = self._serial_factory
        if serial_factory is None:
            try:
                import serial  # type: ignore[import-not-found]
            except ImportError:
                with self._lock:
                    self._last_error = "pyserial belum terpasang"
                return
            serial_factory = serial.Serial

        while not self._stop.is_set():
            try:
                with self._lock:
                    self._connection_attempts += 1
                with serial_factory(self.port, self.baud_rate, timeout=0.5) as connection:
                    with self._lock:
                        self._connected = True
                        self._last_error = None
                    connection.dtr = False
                    connection.rts = False
                    while not self._stop.is_set():
                        raw = connection.readline()
                        if not raw:
                            continue
                        try:
                            payload = json.loads(raw.decode("utf-8", errors="replace"))
                            if payload.get("type") != "sample":
                                continue
                            sample = SensorSample(
                                sensor_id=str(payload["sensor_id"]),
                                received_time_ms=int(time.time() * 1000),
                                device_timestamp_ms=payload.get("timestamp_ms"),
                                distance_cm=payload.get("distance_cm"),
                                valid=bool(payload.get("valid")),
                                status=str(payload.get("status", "unknown")),
                                seq=payload.get("seq"),
                            )
                        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                            continue
                        with self._lock:
                            self._samples.append(sample)
                            self._last_sample_time_ms = sample.received_time_ms
            except Exception as exc:
                with self._lock:
                    self._connected = False
                    self._last_error = str(exc)
                self._stop.wait(self._reconnect_interval_seconds)
            else:
                with self._lock:
                    self._connected = False
