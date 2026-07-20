from __future__ import annotations

from typing import Any

from services.sensor_types import SensorEvidenceStatus


def classify_sensor_evidence(
    evidence: dict[str, Any],
    *,
    max_age_ms: int,
    max_disagreement_cm: float,
) -> dict[str, Any]:
    result = dict(evidence)
    if evidence.get("status") in {"camera_sensor_direction_mismatch", "direction_mismatch"}:
        result["status"] = SensorEvidenceStatus.DIRECTION_MISMATCH.value
        result["reason_code"] = "camera_sensor_direction_mismatch"
        return result
    samples = evidence.get("samples") or {}
    if not evidence.get("enabled", True) or not evidence.get("connected", True):
        result["status"] = SensorEvidenceStatus.UNAVAILABLE.value
        result["reason_code"] = "sensor_bridge_unavailable"
        return result
    valid_samples = [sample for sample in samples.values() if _valid_sample(sample)]
    if not valid_samples:
        result["status"] = SensorEvidenceStatus.STALE.value if evidence.get("last_sample_time_ms") else SensorEvidenceStatus.UNAVAILABLE.value
        result["reason_code"] = "no_valid_sensor_samples"
        return result
    if any(int(sample.get("age_ms", 0)) > max_age_ms for sample in valid_samples):
        result["status"] = SensorEvidenceStatus.STALE.value
        result["reason_code"] = "sensor_sample_stale"
        return result
    if len(valid_samples) >= 2:
        disagreement = abs(float(valid_samples[0]["distance_cm"]) - float(valid_samples[1]["distance_cm"]))
        result["pair_disagreement_cm"] = round(disagreement, 2)
        if disagreement > max_disagreement_cm:
            result["status"] = SensorEvidenceStatus.PAIR_CONFLICT.value
            result["reason_code"] = "sensor_pair_disagreement"
            return result
        result["status"] = SensorEvidenceStatus.PAIRED.value
        return result
    result["status"] = SensorEvidenceStatus.PARTIAL.value
    result["reason_code"] = "one_sensor_sample"
    return result


def _valid_sample(sample: Any) -> bool:
    try:
        return (
            sample.get("status", "ok") == "ok"
            and float(sample["distance_cm"]) >= 0
            and int(sample["age_ms"]) > -1000
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return False
