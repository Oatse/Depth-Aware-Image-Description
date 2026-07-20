from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class CalibrationProfile:
    version: str
    status: str
    validated: bool
    min_capture_count: int
    max_residual_cm: float | None
    sensor_rois: dict[str, dict[str, float]]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CalibrationProfile":
        return cls(
            version=str(payload.get("version", "unknown")),
            status=str(payload.get("status", "unvalidated")),
            validated=bool(payload.get("validated", False)),
            min_capture_count=int(payload.get("min_capture_count", 3)),
            max_residual_cm=payload.get("max_residual_cm"),
            sensor_rois=dict(payload.get("sensor_rois") or {}),
        )

    @classmethod
    def load(cls, path: Path) -> "CalibrationProfile":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


def validate_calibration_measurements(
    measurements: list[dict[str, float]], *, min_capture_count: int = 3, max_residual_cm: float = 10.0
) -> dict[str, Any]:
    if len(measurements) < min_capture_count:
        return {"validated": False, "status": "insufficient_captures", "capture_count": len(measurements)}
    distinct_references = {round(float(item["measured_cm"]), 1) for item in measurements}
    if len(distinct_references) < min_capture_count:
        return {
            "validated": False,
            "status": "insufficient_reference_distances",
            "capture_count": len(measurements),
            "distinct_reference_count": len(distinct_references),
        }
    residuals = [abs(float(item["measured_cm"]) - float(item["sensor_cm"])) for item in measurements]
    residual = max(residuals)
    return {
        "validated": residual <= max_residual_cm,
        "status": "validated" if residual <= max_residual_cm else "residual_exceeds_gate",
        "capture_count": len(measurements),
        "distinct_reference_count": len(distinct_references),
        "max_residual_cm": round(residual, 3),
    }


def build_calibration_profile(
    measurements: list[dict[str, Any]], *, min_capture_count: int = 3, max_residual_cm: float = 10.0
) -> dict[str, Any]:
    validation = validate_calibration_measurements(
        measurements,
        min_capture_count=min_capture_count,
        max_residual_cm=max_residual_cm,
    )
    return {
        "version": f"frontal-distance-v1-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
        **validation,
        "min_capture_count": min_capture_count,
        "residual_gate_cm": max_residual_cm,
        "measurement_kind": "frontal_planar_distance",
        "sensor_rois": {},
        "measurements": measurements,
    }


def load_measurements(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Calibration measurements must be a JSON array.")
    return [dict(item) for item in payload]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(path)
