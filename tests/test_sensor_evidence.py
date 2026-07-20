from services.sensor_evidence import collect_sensor_evidence


class RecordingSensorBridge:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def snapshot(self, capture_time_ms: int, window_ms: int) -> dict[str, object]:
        self.calls.append((capture_time_ms, window_ms))
        return {
            "enabled": True,
            "connected": True,
            "status": "paired",
            "samples": {
                "sensor_1": {"distance_cm": 42.3},
                "sensor_2": {"distance_cm": 43.1},
            },
        }


def test_capture_uses_client_frame_time_when_clock_is_aligned() -> None:
    bridge = RecordingSensorBridge()

    evidence = collect_sensor_evidence(
        bridge,
        capture_id="cap-001",
        client_capture_time_ms=1_000_000,
        camera_facing_mode="environment",
        match_window_ms=250,
        max_clock_skew_ms=5_000,
        now_ms=1_000_065,
    )

    assert bridge.calls == [(1_000_000, 250)]
    assert evidence is not None
    assert evidence["match_time_source"] == "client_capture"
    assert evidence["capture_transport_delay_ms"] == 65
    assert evidence["capture_id"] == "cap-001"


def test_capture_falls_back_to_host_time_when_client_clock_is_not_aligned() -> None:
    bridge = RecordingSensorBridge()

    evidence = collect_sensor_evidence(
        bridge,
        capture_id="cap-skewed",
        client_capture_time_ms=900_000,
        camera_facing_mode="environment",
        match_window_ms=250,
        max_clock_skew_ms=5_000,
        now_ms=1_000_000,
    )

    assert bridge.calls == [(1_000_000, 250)]
    assert evidence is not None
    assert evidence["match_time_source"] == "host_receive_fallback"
    assert evidence["clock_skew_exceeded"] is True


def test_front_camera_capture_is_not_paired_with_forward_sensors() -> None:
    bridge = RecordingSensorBridge()

    evidence = collect_sensor_evidence(
        bridge,
        capture_id="cap-front",
        client_capture_time_ms=1_000_000,
        camera_facing_mode="user",
        match_window_ms=250,
        max_clock_skew_ms=5_000,
        now_ms=1_000_030,
    )

    assert bridge.calls == []
    assert evidence is not None
    assert evidence["status"] == "camera_sensor_direction_mismatch"
    assert evidence["samples"] == {}
