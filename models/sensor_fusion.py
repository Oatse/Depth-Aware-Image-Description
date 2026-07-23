from __future__ import annotations

import math

from services.sensor_calibration import CalibrationProfile
from services.sensor_types import SensorContribution


def fuse_sensor_reference(
    sensor_evidence: dict | None,
    *,
    calibration_profile: CalibrationProfile | None,
    max_pair_disagreement_cm: float,
    max_age_ms: int,
) -> SensorContribution:
    correction_ready = calibration_profile is not None and calibration_profile.correction_ready
    calibration_status = "validated" if correction_ready else "not_validated"
    calibration_version = calibration_profile.version if calibration_profile is not None else None
    if not sensor_evidence:
        return _insufficient(
            "sensor_unavailable",
            "Referensi sensor frontal tidak tersedia.",
            calibration_status=calibration_status,
            calibration_version=calibration_version,
        )

    status = str(sensor_evidence.get("status") or "unavailable")
    samples = sensor_evidence.get("samples") or {}
    values = _sensor_values(samples)
    sensor_1 = values.get("sensor_1")
    sensor_2 = values.get("sensor_2")
    disagreement = (
        round(abs(sensor_1 - sensor_2), 2)
        if sensor_1 is not None and sensor_2 is not None
        else None
    )
    if status in {"direction_mismatch", "camera_sensor_direction_mismatch"}:
        return _insufficient(
            "camera_sensor_direction_mismatch",
            "Referensi jarak frontal ditahan karena arah kamera tidak sesuai dengan arah sensor.",
            sensor_1=sensor_1,
            sensor_2=sensor_2,
            disagreement=disagreement,
            calibration_status=calibration_status,
            calibration_version=calibration_version,
        )
    if status == "pair_conflict":
        return {
            "status": "conflict",
            "reason_code": "sensor_pair_disagreement",
            "sensor_1_cm": sensor_1,
            "sensor_2_cm": sensor_2,
            "sensor_1_corrected_cm": None,
            "sensor_2_corrected_cm": None,
            "frontal_reference_cm": None,
            "pair_disagreement_cm": disagreement,
            "calibration_status": calibration_status,
            "calibration_version": calibration_version,
            "description": "Referensi jarak frontal ditahan karena dua sensor tidak konsisten.",
            "warnings": ["Nilai individual tersedia pada provenance untuk pemeriksaan."],
        }
    if status == "partial":
        sensor_id, value = next(iter(values.items()), (None, None))
        label = "Sensor 1" if sensor_id == "sensor_1" else "Sensor 2"
        description = (
            f"{label} membaca {value:.1f} cm; nilai ini bukan rata-rata pasangan sensor."
            if value is not None
            else "Hanya satu kanal sensor tersedia; referensi rata-rata tidak dibentuk."
        )
        return {
            "status": "partial",
            "reason_code": sensor_evidence.get("reason_code") or "one_sensor_sample",
            "sensor_1_cm": sensor_1,
            "sensor_2_cm": sensor_2,
            "sensor_1_corrected_cm": None,
            "sensor_2_corrected_cm": None,
            "frontal_reference_cm": None,
            "pair_disagreement_cm": None,
            "calibration_status": calibration_status,
            "calibration_version": calibration_version,
            "description": description,
            "warnings": ["Nilai berasal dari satu kanal sensor."],
        }
    if status != "paired" or sensor_1 is None or sensor_2 is None:
        return _insufficient(
            sensor_evidence.get("reason_code") or f"sensor_{status}",
            "Referensi jarak frontal ditahan karena evidence tidak lengkap atau tidak segar.",
            sensor_1=sensor_1,
            sensor_2=sensor_2,
            disagreement=disagreement,
            calibration_status=calibration_status,
            calibration_version=calibration_version,
        )
    if not _fresh_pair(samples, max_age_ms):
        return _insufficient(
            "sensor_sample_stale",
            "Referensi jarak frontal ditahan karena pasangan sensor tidak segar.",
            sensor_1=sensor_1,
            sensor_2=sensor_2,
            disagreement=disagreement,
            calibration_status=calibration_status,
            calibration_version=calibration_version,
        )
    if disagreement is None or disagreement > max_pair_disagreement_cm:
        return {
            "status": "conflict",
            "reason_code": "sensor_pair_disagreement",
            "sensor_1_cm": sensor_1,
            "sensor_2_cm": sensor_2,
            "sensor_1_corrected_cm": None,
            "sensor_2_corrected_cm": None,
            "frontal_reference_cm": None,
            "pair_disagreement_cm": disagreement,
            "calibration_status": calibration_status,
            "calibration_version": calibration_version,
            "description": "Referensi jarak frontal ditahan karena dua sensor tidak konsisten.",
            "warnings": ["Nilai individual tersedia pada provenance untuk pemeriksaan."],
        }

    if not correction_ready or calibration_profile is None:
        return _insufficient(
            "calibration_not_validated",
            "Referensi jarak frontal ditahan karena model koreksi kalibrasi belum tersedia.",
            sensor_1=sensor_1,
            sensor_2=sensor_2,
            disagreement=disagreement,
            calibration_status=calibration_status,
            calibration_version=calibration_version,
        )

    sensor_1_corrected = round(calibration_profile.correct("sensor_1", sensor_1), 2)
    sensor_2_corrected = round(calibration_profile.correct("sensor_2", sensor_2), 2)
    reference = round((sensor_1_corrected + sensor_2_corrected) / 2, 2)
    return {
        "status": "applied",
        "reason_code": None,
        "sensor_1_cm": sensor_1,
        "sensor_2_cm": sensor_2,
        "sensor_1_corrected_cm": sensor_1_corrected,
        "sensor_2_corrected_cm": sensor_2_corrected,
        "frontal_reference_cm": reference,
        "pair_disagreement_cm": disagreement,
        "calibration_status": calibration_status,
        "calibration_version": calibration_version,
        "description": f"Referensi jarak frontal sekitar {reference:.1f} cm pada arah sensor.",
        "warnings": [],
    }


def append_sensor_section(
    base_description: str | None,
    contribution: SensorContribution,
    structured: dict | None = None,
) -> str:
    base = (base_description or "Deskripsi visual-spasial tidak tersedia.").strip()
    if (
        contribution
        and contribution["status"] == "applied"
        and float(contribution.get("pair_disagreement_cm") or 999.0) <= 2.0
    ):
        closest = str((structured or {}).get("closest_object") or "").strip()
        if closest and closest.lower() not in {"tidak_diketahui", "tidak ada", "unknown", "none"}:
            return f"{base} {closest} tampak sebagai objek paling dekat di depan kamera, dengan estimasi jarak sekitar {contribution['frontal_reference_cm']:.1f} cm."
    return f"{base} {contribution['description']}" if contribution else base


def _insufficient(
    reason_code: str,
    description: str,
    *,
    sensor_1: float | None = None,
    sensor_2: float | None = None,
    disagreement: float | None = None,
    calibration_status: str = "not_validated",
    calibration_version: str | None = None,
) -> SensorContribution:
    return {
        "status": "insufficient",
        "reason_code": reason_code,
        "sensor_1_cm": sensor_1,
        "sensor_2_cm": sensor_2,
        "sensor_1_corrected_cm": None,
        "sensor_2_corrected_cm": None,
        "frontal_reference_cm": None,
        "pair_disagreement_cm": disagreement,
        "calibration_status": calibration_status,
        "calibration_version": calibration_version,
        "description": description,
        "warnings": [],
    }


def _sensor_values(samples: dict) -> dict[str, float]:
    values: dict[str, float] = {}
    for sensor_id in ("sensor_1", "sensor_2"):
        sample = samples.get(sensor_id) or {}
        if sample.get("status", "ok") != "ok":
            continue
        try:
            value = float(sample["distance_cm"])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(value) and value >= 0:
            values[sensor_id] = round(value, 2)
    return values


def _fresh_pair(samples: dict, max_age_ms: int) -> bool:
    for sensor_id in ("sensor_1", "sensor_2"):
        sample = samples.get(sensor_id) or {}
        if sample.get("status", "ok") != "ok":
            return False
        try:
            if abs(int(sample["age_ms"])) > max_age_ms:
                return False
        except (KeyError, TypeError, ValueError):
            return False
    return True
