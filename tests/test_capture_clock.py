import pytest

from services.capture_clock import CaptureClock, choose_clock_sample, normalize_capture_time


def test_normalizes_fast_client_clock() -> None:
    normalized = normalize_capture_time(
        1_000,
        CaptureClock(offset_ms=250, rtt_ms=20),
        host_receive_time_ms=1_400,
        max_rtt_ms=100,
    )
    assert normalized.capture_time_ms == 1_250
    assert normalized.source == "normalized_client_capture"


def test_high_rtt_uses_explicit_host_fallback() -> None:
    normalized = normalize_capture_time(
        1_000,
        CaptureClock(offset_ms=250, rtt_ms=101),
        host_receive_time_ms=1_400,
        max_rtt_ms=100,
    )
    assert normalized.capture_time_ms == 1_400
    assert normalized.reason_code == "clock_rtt_high"


def test_choose_lowest_rtt_and_reject_invalid_capture_time() -> None:
    assert choose_clock_sample([CaptureClock(100, 40), CaptureClock(120, 10)]).offset_ms == 120
    with pytest.raises(ValueError, match="client_capture_time_ms"):
        normalize_capture_time(-1, None, host_receive_time_ms=1, max_rtt_ms=100)
