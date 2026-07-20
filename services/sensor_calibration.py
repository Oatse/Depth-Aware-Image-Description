from __future__ import annotations

import json
from dataclasses import dataclass
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
    residuals = [abs(float(item["measured_cm"]) - float(item["sensor_cm"])) for item in measurements]
    residual = max(residuals)
    return {
        "validated": residual <= max_residual_cm,
        "status": "validated" if residual <= max_residual_cm else "residual_exceeds_gate",
        "capture_count": len(measurements),
        "max_residual_cm": round(residual, 3),
    }
