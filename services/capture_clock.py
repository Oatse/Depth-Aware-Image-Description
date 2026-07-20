from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CaptureClock:
    offset_ms: int
    rtt_ms: int


@dataclass(frozen=True, slots=True)
class NormalizedCaptureTime:
    capture_time_ms: int
    source: str
    reason_code: str | None = None


def normalize_capture_time(
    client_capture_time_ms: int,
    clock: CaptureClock | None,
    *,
    host_receive_time_ms: int,
    max_rtt_ms: int,
) -> NormalizedCaptureTime:
    if client_capture_time_ms < 0:
        raise ValueError("client_capture_time_ms must be non-negative")
    if clock is None:
        return NormalizedCaptureTime(host_receive_time_ms, "host_receive_fallback", "clock_sync_missing")
    if clock.rtt_ms < 0:
        raise ValueError("rtt_ms must be non-negative")
    if clock.rtt_ms > max_rtt_ms:
        return NormalizedCaptureTime(host_receive_time_ms, "host_receive_fallback", "clock_rtt_high")
    return NormalizedCaptureTime(
        client_capture_time_ms + clock.offset_ms,
        "normalized_client_capture",
    )


def choose_clock_sample(samples: list[CaptureClock]) -> CaptureClock | None:
    if not samples:
        return None
    return min(samples, key=lambda sample: sample.rtt_ms)
