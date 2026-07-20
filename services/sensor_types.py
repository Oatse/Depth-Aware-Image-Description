from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class SensorEvidenceStatus(StrEnum):
    PAIRED = "paired"
    PARTIAL = "partial"
    PAIR_CONFLICT = "pair_conflict"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    DIRECTION_MISMATCH = "direction_mismatch"


class SensorContributionStatus(StrEnum):
    APPLIED = "applied"
    CONFLICT = "conflict"
    INSUFFICIENT = "insufficient"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class SensorSample:
    sensor_id: str
    distance_cm: float
    received_time_ms: int
    age_ms: int
    status: str = "ok"

    def __post_init__(self) -> None:
        if not self.sensor_id.strip():
            raise ValueError("sensor_id must not be empty")
        if self.distance_cm < 0:
            raise ValueError("distance_cm must be non-negative")
        if self.received_time_ms < 0:
            raise ValueError("received_time_ms must be non-negative")
        if self.age_ms < 0:
            raise ValueError("age_ms must be non-negative")


@dataclass(frozen=True, slots=True)
class SensorEvidence:
    capture_id: str
    status: SensorEvidenceStatus
    samples: dict[str, SensorSample]
    capture_time_ms: int | None = None
    match_time_ms: int | None = None
    match_time_source: str | None = None
    camera_facing_mode: str | None = None
    pair_disagreement_cm: float | None = None
    reason_code: str | None = None

    def __post_init__(self) -> None:
        if not self.capture_id.strip():
            raise ValueError("capture_id is required for sensor evidence")
        if self.pair_disagreement_cm is not None and self.pair_disagreement_cm < 0:
            raise ValueError("pair_disagreement_cm must be non-negative")


def sensor_evidence_from_payload(payload: dict[str, Any]) -> SensorEvidence:
    samples = {
        sensor_id: SensorSample(
            sensor_id=sensor_id,
            distance_cm=float(sample["distance_cm"]),
            received_time_ms=int(sample["received_time_ms"]),
            age_ms=int(sample["age_ms"]),
            status=str(sample.get("status", "ok")),
        )
        for sensor_id, sample in (payload.get("samples") or {}).items()
    }
    raw_status = str(payload.get("status", SensorEvidenceStatus.UNAVAILABLE))
    legacy_status = {
        "sensor_pair_conflict": SensorEvidenceStatus.PAIR_CONFLICT,
        "sensor_unavailable": SensorEvidenceStatus.UNAVAILABLE,
        "camera_sensor_direction_mismatch": SensorEvidenceStatus.DIRECTION_MISMATCH,
    }
    status = legacy_status.get(raw_status, raw_status)
    return SensorEvidence(
        capture_id=str(payload.get("capture_id") or ""),
        status=SensorEvidenceStatus(status),
        samples=samples,
        capture_time_ms=payload.get("capture_time_ms", payload.get("client_capture_time_ms")),
        match_time_ms=payload.get("match_time_ms"),
        match_time_source=payload.get("match_time_source"),
        camera_facing_mode=payload.get("camera_facing_mode"),
        pair_disagreement_cm=payload.get("pair_disagreement_cm"),
        reason_code=payload.get("reason_code"),
    )
