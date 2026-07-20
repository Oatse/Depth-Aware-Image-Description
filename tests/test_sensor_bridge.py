from __future__ import annotations

import json
import time
from collections import deque

from services.sensor_bridge import SensorBridge


class _FakeSerialConnection:
    def __init__(self) -> None:
        self.dtr = True
        self.rts = True
        self._lines = deque(
            [
                json.dumps(
                    {
                        "type": "sample",
                        "sensor_id": "sensor_1",
                        "timestamp_ms": 100,
                        "distance_cm": 84.2,
                        "valid": True,
                        "status": "ok",
                        "seq": 1,
                    }
                ).encode()
                + b"\n",
                json.dumps(
                    {
                        "type": "sample",
                        "sensor_id": "sensor_2",
                        "timestamp_ms": 110,
                        "distance_cm": 86.5,
                        "valid": True,
                        "status": "ok",
                        "seq": 2,
                    }
                ).encode()
                + b"\n",
            ]
        )

    def __enter__(self) -> _FakeSerialConnection:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def readline(self) -> bytes:
        if self._lines:
            return self._lines.popleft()
        time.sleep(0.005)
        return b""


class _FlakySerialFactory:
    def __init__(self) -> None:
        self.attempts = 0

    def __call__(self, _port: str, _baud_rate: int, *, timeout: float) -> _FakeSerialConnection:
        assert timeout == 0.5
        self.attempts += 1
        if self.attempts == 1:
            raise OSError("device belum tersedia")
        return _FakeSerialConnection()


def test_bridge_reconnects_and_exposes_live_pair_after_initial_failure() -> None:
    serial_factory = _FlakySerialFactory()
    bridge = SensorBridge(
        "COM7",
        115200,
        serial_factory=serial_factory,
        reconnect_interval_seconds=0.01,
    )

    bridge.start()
    deadline = time.monotonic() + 1
    evidence = bridge.snapshot(int(time.time() * 1000), 1000)
    while evidence["status"] != "paired" and time.monotonic() < deadline:
        time.sleep(0.01)
        evidence = bridge.snapshot(int(time.time() * 1000), 1000)
    bridge.stop()

    assert serial_factory.attempts >= 2
    assert evidence["connected"] is True
    assert evidence["connection_attempts"] >= 2
    assert evidence["reader_error"] is None
    assert evidence["status"] == "paired"
    assert evidence["samples"]["sensor_1"]["distance_cm"] == 84.2
    assert evidence["samples"]["sensor_2"]["distance_cm"] == 86.5
