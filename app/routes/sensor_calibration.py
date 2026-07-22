from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.config import get_settings
from services.sensor_calibration import (
    CalibrationProfile,
    build_calibration_profile,
    build_verification_summary,
    calibration_reference_overlap,
    load_measurements,
    verification_reference_allowed,
    write_json,
)


router = APIRouter(tags=["Sensor IoT"])
settings = get_settings()


class CalibrationCaptureRequest(BaseModel):
    measured_cm: float = Field(gt=5, le=400)


class VerificationCaptureRequest(BaseModel):
    measured_cm: float = Field(gt=5, le=200)


@router.get("/sensor-calibration")
async def sensor_calibration_status() -> dict[str, Any]:
    measurements = load_measurements(settings.sensor_calibration_measurements_path)
    profile = build_calibration_profile(measurements)
    if measurements:
        write_json(settings.sensor_calibration_path, profile)
    return {"success": True, "profile": profile, "measurements": measurements}


@router.post("/sensor-calibration/captures")
async def capture_sensor_calibration(payload: CalibrationCaptureRequest, request: Request) -> dict[str, Any]:
    measurements = load_measurements(settings.sensor_calibration_measurements_path)
    existing_profile = build_calibration_profile(measurements)
    if existing_profile["validated"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kalibrasi 5 x 30 sudah lengkap dan dibekukan. Reset kalibrasi untuk memulai ulang.",
        )

    snapshot, sensor_1_cm, sensor_2_cm = _paired_snapshot(request)
    sensor_cm = round((sensor_1_cm + sensor_2_cm) / 2, 3)
    measurement = {
        "captured_at_ms": int(time.time() * 1000),
        "measured_cm": round(payload.measured_cm, 3),
        "sensor_1_cm": round(sensor_1_cm, 3),
        "sensor_2_cm": round(sensor_2_cm, 3),
        "sensor_cm": sensor_cm,
        "residual_cm": round(abs(payload.measured_cm - sensor_cm), 3),
        **_snapshot_provenance(snapshot),
    }
    measurements.append(measurement)
    profile = build_calibration_profile(measurements)
    write_json(settings.sensor_calibration_measurements_path, measurements)
    write_json(settings.sensor_calibration_path, profile)
    return {"success": True, "measurement": measurement, "profile": profile, "measurements": measurements}


@router.delete("/sensor-calibration")
async def reset_sensor_calibration() -> dict[str, Any]:
    removed = []
    paths = (
        settings.sensor_calibration_measurements_path,
        settings.sensor_calibration_path,
        settings.sensor_verification_measurements_path,
        settings.sensor_verification_path,
    )
    for path in paths:
        if path.exists():
            path.unlink()
            removed.append(path.name)
    return {"success": True, "removed": removed}


@router.get("/sensor-calibration/verification")
async def sensor_verification_status() -> dict[str, Any]:
    calibration = _load_current_calibration()
    measurements = load_measurements(settings.sensor_verification_measurements_path)
    summary = build_verification_summary(measurements, calibration)
    if measurements:
        write_json(settings.sensor_verification_path, summary)
    return {"success": True, "summary": summary, "measurements": measurements}


@router.post("/sensor-calibration/verification/captures")
async def capture_sensor_verification(payload: VerificationCaptureRequest, request: Request) -> dict[str, Any]:
    calibration = _load_current_calibration()
    if not verification_reference_allowed(payload.measured_cm):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Protokol verifikasi aktif hanya memakai 40, 80, 125, dan 175 cm dalam batas operasional sampai 200 cm.",
        )
    if calibration_reference_overlap(calibration, payload.measured_cm):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Jarak verifikasi harus berbeda dari titik kalibrasi 20, 60, 100, 150, dan 200 cm.",
        )

    snapshot, sensor_1_raw, sensor_2_raw = _paired_snapshot(request)
    measurements = load_measurements(settings.sensor_verification_measurements_path)
    provenance = _snapshot_provenance(snapshot)
    if _duplicates_latest_sequence(measurements, calibration.version, provenance):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pembacaan sensor ini sudah dicatat. Tunggu sequence sensor berikutnya.",
        )

    sensor_1_corrected = calibration.correct("sensor_1", sensor_1_raw)
    sensor_2_corrected = calibration.correct("sensor_2", sensor_2_raw)
    raw_frontal = (sensor_1_raw + sensor_2_raw) / 2
    corrected_frontal = (sensor_1_corrected + sensor_2_corrected) / 2
    measurement = {
        "captured_at_ms": int(time.time() * 1000),
        "calibration_version": calibration.version,
        "measured_cm": round(payload.measured_cm, 3),
        "sensor_1_raw_cm": round(sensor_1_raw, 3),
        "sensor_2_raw_cm": round(sensor_2_raw, 3),
        "sensor_1_corrected_cm": round(sensor_1_corrected, 3),
        "sensor_2_corrected_cm": round(sensor_2_corrected, 3),
        "raw_frontal_cm": round(raw_frontal, 3),
        "corrected_frontal_cm": round(corrected_frontal, 3),
        "raw_residual_cm": round(abs(payload.measured_cm - raw_frontal), 3),
        "corrected_residual_cm": round(abs(payload.measured_cm - corrected_frontal), 3),
        **provenance,
    }
    measurements.append(measurement)
    summary = build_verification_summary(measurements, calibration)
    write_json(settings.sensor_verification_measurements_path, measurements)
    write_json(settings.sensor_verification_path, summary)
    return {"success": True, "measurement": measurement, "summary": summary, "measurements": measurements}


@router.delete("/sensor-calibration/verification")
async def reset_sensor_verification() -> dict[str, Any]:
    removed = []
    for path in (settings.sensor_verification_measurements_path, settings.sensor_verification_path):
        if path.exists():
            path.unlink()
            removed.append(path.name)
    return {"success": True, "removed": removed}


def _load_current_calibration() -> CalibrationProfile:
    measurements = load_measurements(settings.sensor_calibration_measurements_path)
    profile_payload = build_calibration_profile(measurements)
    profile = CalibrationProfile.from_dict(profile_payload)
    if not profile.correction_ready:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kalibrasi 5 jarak x 30 pembacaan belum lengkap atau belum valid.",
        )
    write_json(settings.sensor_calibration_path, profile_payload)
    return profile


def _paired_snapshot(request: Request) -> tuple[dict[str, Any], float, float]:
    sensor_bridge = getattr(request.app.state, "sensor_bridge", None)
    if sensor_bridge is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sensor bridge tidak tersedia.")
    snapshot = sensor_bridge.snapshot(int(time.time() * 1000), settings.sensor_status_window_ms)
    if snapshot.get("status") != "paired":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dua sensor harus paired dan segar.")
    samples = snapshot.get("samples") or {}
    try:
        sensor_1_cm = float(samples["sensor_1"]["distance_cm"])
        sensor_2_cm = float(samples["sensor_2"]["distance_cm"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bacaan dua sensor tidak lengkap.") from exc
    return snapshot, sensor_1_cm, sensor_2_cm


def _snapshot_provenance(snapshot: dict[str, Any]) -> dict[str, Any]:
    samples = snapshot.get("samples") or {}
    sensor_1 = samples.get("sensor_1") or {}
    sensor_2 = samples.get("sensor_2") or {}
    return {
        "sensor_1_seq": sensor_1.get("seq"),
        "sensor_2_seq": sensor_2.get("seq"),
        "sensor_1_received_time_ms": sensor_1.get("received_time_ms"),
        "sensor_2_received_time_ms": sensor_2.get("received_time_ms"),
    }


def _duplicates_latest_sequence(
    measurements: list[dict[str, Any]], calibration_version: str, provenance: dict[str, Any]
) -> bool:
    if not measurements or provenance["sensor_1_seq"] is None or provenance["sensor_2_seq"] is None:
        return False
    latest = measurements[-1]
    return (
        latest.get("calibration_version") == calibration_version
        and latest.get("sensor_1_seq") == provenance["sensor_1_seq"]
        and latest.get("sensor_2_seq") == provenance["sensor_2_seq"]
    )
