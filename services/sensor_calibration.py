from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean
from typing import Any


MIN_CALIBRATION_REFERENCE_COUNT = 5
MIN_CALIBRATION_SAMPLES_PER_REFERENCE = 30
VERIFICATION_REFERENCE_DISTANCES_CM = (40.0, 80.0, 125.0, 175.0)
MAX_OPERATIONAL_DISTANCE_CM = 200.0
MIN_VERIFICATION_REFERENCE_COUNT = len(VERIFICATION_REFERENCE_DISTANCES_CM)
MIN_VERIFICATION_SAMPLES_PER_REFERENCE = 30
MAX_RESIDUAL_CM = 10.0


@dataclass(frozen=True, slots=True)
class CalibrationProfile:
    version: str
    status: str
    validated: bool
    min_reference_count: int
    min_samples_per_reference: int
    max_residual_cm: float | None
    reference_distances_cm: tuple[float, ...]
    correction_model: dict[str, dict[str, float]]
    sensor_rois: dict[str, dict[str, float]]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CalibrationProfile":
        correction_model = payload.get("correction_model") or {}
        return cls(
            version=str(payload.get("version", "unknown")),
            status=str(payload.get("status", "unvalidated")),
            validated=bool(payload.get("validated", False)),
            min_reference_count=int(payload.get("min_reference_count", MIN_CALIBRATION_REFERENCE_COUNT)),
            min_samples_per_reference=int(
                payload.get("min_samples_per_reference", MIN_CALIBRATION_SAMPLES_PER_REFERENCE)
            ),
            max_residual_cm=payload.get("max_residual_cm"),
            reference_distances_cm=tuple(float(value) for value in payload.get("reference_distances_cm", [])),
            correction_model={str(key): dict(value) for key, value in correction_model.items()},
            sensor_rois=dict(payload.get("sensor_rois") or {}),
        )

    @classmethod
    def load(cls, path: Path) -> "CalibrationProfile":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

    @property
    def correction_ready(self) -> bool:
        return self.validated and all(sensor_id in self.correction_model for sensor_id in ("sensor_1", "sensor_2"))

    def correct(self, sensor_id: str, raw_cm: float) -> float:
        if not self.correction_ready:
            raise ValueError("Calibration correction model is not ready.")
        model = self.correction_model.get(sensor_id)
        if model is None:
            raise ValueError(f"No correction model is available for {sensor_id}.")
        return float(model["intercept"]) + float(model["slope"]) * float(raw_cm)


def validate_calibration_measurements(
    measurements: list[dict[str, float]],
    *,
    min_reference_count: int = MIN_CALIBRATION_REFERENCE_COUNT,
    min_samples_per_reference: int = MIN_CALIBRATION_SAMPLES_PER_REFERENCE,
    max_residual_cm: float = MAX_RESIDUAL_CM,
) -> dict[str, Any]:
    counts = _reference_counts(measurements)
    capture_count = len(measurements)
    common = {
        "capture_count": capture_count,
        "distinct_reference_count": len(counts),
        "reference_counts": {format(reference, "g"): count for reference, count in counts.items()},
    }
    if len(counts) < min_reference_count:
        return {"validated": False, "status": "insufficient_reference_distances", **common}
    insufficient = {reference: count for reference, count in counts.items() if count < min_samples_per_reference}
    if insufficient:
        return {
            "validated": False,
            "status": "insufficient_samples_per_reference",
            "insufficient_reference_counts": {
                format(reference, "g"): count for reference, count in insufficient.items()
            },
            **common,
        }
    try:
        residuals = [abs(float(item["measured_cm"]) - float(item["sensor_cm"])) for item in measurements]
    except (KeyError, TypeError, ValueError):
        return {"validated": False, "status": "invalid_measurements", **common}
    max_residual = max(residuals, default=math.inf)
    return {
        "validated": max_residual <= max_residual_cm,
        "status": "validated" if max_residual <= max_residual_cm else "residual_exceeds_gate",
        "max_residual_cm": round(max_residual, 3),
        **common,
    }


def build_calibration_profile(
    measurements: list[dict[str, Any]],
    *,
    min_reference_count: int = MIN_CALIBRATION_REFERENCE_COUNT,
    min_samples_per_reference: int = MIN_CALIBRATION_SAMPLES_PER_REFERENCE,
    max_residual_cm: float = MAX_RESIDUAL_CM,
) -> dict[str, Any]:
    validation = validate_calibration_measurements(
        measurements,
        min_reference_count=min_reference_count,
        min_samples_per_reference=min_samples_per_reference,
        max_residual_cm=max_residual_cm,
    )
    correction_model: dict[str, dict[str, float]] = {}
    if validation["validated"]:
        correction_model = {
            sensor_id: _linear_fit(measurements, sensor_field)
            for sensor_id, sensor_field in (
                ("sensor_1", "sensor_1_cm"),
                ("sensor_2", "sensor_2_cm"),
                ("frontal", "sensor_cm"),
            )
        }
    references = sorted({round(float(item["measured_cm"]), 3) for item in measurements})
    return {
        "version": _profile_version(measurements),
        **validation,
        "min_reference_count": min_reference_count,
        "min_samples_per_reference": min_samples_per_reference,
        "residual_gate_cm": max_residual_cm,
        "measurement_kind": "frontal_planar_distance",
        "reference_distances_cm": references,
        "correction_model": correction_model,
        "sensor_rois": {},
        "measurements": measurements,
    }


def build_verification_summary(
    measurements: list[dict[str, Any]],
    calibration: CalibrationProfile,
    *,
    min_reference_count: int = MIN_VERIFICATION_REFERENCE_COUNT,
    min_samples_per_reference: int = MIN_VERIFICATION_SAMPLES_PER_REFERENCE,
    max_residual_cm: float = MAX_RESIDUAL_CM,
) -> dict[str, Any]:
    current = [
        item
        for item in measurements
        if item.get("calibration_version") == calibration.version
        and _matches_reference(float(item.get("measured_cm", -1)), VERIFICATION_REFERENCE_DISTANCES_CM)
    ]
    counts = _reference_counts(current)
    common = {
        "calibration_version": calibration.version,
        "capture_count": len(current),
        "distinct_reference_count": len(counts),
        "reference_counts": {format(reference, "g"): count for reference, count in counts.items()},
        "min_reference_count": min_reference_count,
        "min_samples_per_reference": min_samples_per_reference,
        "required_reference_distances_cm": list(VERIFICATION_REFERENCE_DISTANCES_CM),
        "max_operational_distance_cm": MAX_OPERATIONAL_DISTANCE_CM,
    }
    if any(reference not in counts for reference in VERIFICATION_REFERENCE_DISTANCES_CM):
        return {"verified": False, "status": "insufficient_reference_distances", **common}
    if any(counts[reference] < min_samples_per_reference for reference in VERIFICATION_REFERENCE_DISTANCES_CM):
        return {"verified": False, "status": "insufficient_samples_per_reference", **common}

    raw_errors = [float(item["raw_frontal_cm"]) - float(item["measured_cm"]) for item in current]
    corrected_errors = [float(item["corrected_frontal_cm"]) - float(item["measured_cm"]) for item in current]
    raw_metrics = _error_metrics(raw_errors)
    corrected_metrics = _error_metrics(corrected_errors)
    improved = corrected_metrics["mae_cm"] < raw_metrics["mae_cm"]
    within_gate = corrected_metrics["max_abs_error_cm"] <= max_residual_cm
    return {
        "verified": improved and within_gate,
        "status": "verified" if improved and within_gate else "verification_failed",
        "raw_metrics": raw_metrics,
        "corrected_metrics": corrected_metrics,
        "improved": improved,
        "within_residual_gate": within_gate,
        "residual_gate_cm": max_residual_cm,
        "points": _verification_point_summaries(current),
        **common,
    }


def calibration_reference_overlap(calibration: CalibrationProfile, measured_cm: float, tolerance_cm: float = 0.05) -> bool:
    return any(abs(reference - measured_cm) <= tolerance_cm for reference in calibration.reference_distances_cm)


def verification_reference_allowed(measured_cm: float, tolerance_cm: float = 0.05) -> bool:
    return _matches_reference(measured_cm, VERIFICATION_REFERENCE_DISTANCES_CM, tolerance_cm)


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


def _reference_counts(measurements: list[dict[str, Any]]) -> dict[float, int]:
    counts: dict[float, int] = {}
    for item in measurements:
        try:
            reference = round(float(item["measured_cm"]), 3)
        except (KeyError, TypeError, ValueError):
            continue
        counts[reference] = counts.get(reference, 0) + 1
    return dict(sorted(counts.items()))


def _matches_reference(
    measured_cm: float,
    references: tuple[float, ...],
    tolerance_cm: float = 0.05,
) -> bool:
    return any(abs(reference - measured_cm) <= tolerance_cm for reference in references)


def _linear_fit(measurements: list[dict[str, Any]], sensor_field: str) -> dict[str, float]:
    pairs = [(float(item[sensor_field]), float(item["measured_cm"])) for item in measurements]
    raw_values = [pair[0] for pair in pairs]
    references = [pair[1] for pair in pairs]
    raw_mean = fmean(raw_values)
    reference_mean = fmean(references)
    denominator = sum((value - raw_mean) ** 2 for value in raw_values)
    if denominator == 0:
        raise ValueError(f"Cannot fit calibration model for {sensor_field}: sensor values are constant.")
    slope = sum(
        (raw - raw_mean) * (reference - reference_mean)
        for raw, reference in pairs
    ) / denominator
    intercept = reference_mean - slope * raw_mean
    predictions = [intercept + slope * raw for raw in raw_values]
    errors = [prediction - reference for prediction, reference in zip(predictions, references, strict=True)]
    total_variation = sum((reference - reference_mean) ** 2 for reference in references)
    residual_variation = sum(error**2 for error in errors)
    return {
        "intercept": round(intercept, 9),
        "slope": round(slope, 9),
        "r2": round(1 - residual_variation / total_variation, 9),
        "training_mae_cm": round(fmean(abs(error) for error in errors), 3),
        "training_rmse_cm": round(math.sqrt(fmean(error**2 for error in errors)), 3),
    }


def _profile_version(measurements: list[dict[str, Any]]) -> str:
    canonical = json.dumps(measurements, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()[:12]
    return f"frontal-distance-v2-{digest}"


def _error_metrics(errors: list[float]) -> dict[str, float]:
    return {
        "bias_cm": round(fmean(errors), 3),
        "mae_cm": round(fmean(abs(error) for error in errors), 3),
        "rmse_cm": round(math.sqrt(fmean(error**2 for error in errors)), 3),
        "max_abs_error_cm": round(max(abs(error) for error in errors), 3),
    }


def _verification_point_summaries(measurements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[float, list[dict[str, Any]]] = {}
    for item in measurements:
        grouped.setdefault(round(float(item["measured_cm"]), 3), []).append(item)
    summaries = []
    for reference, items in sorted(grouped.items()):
        raw_errors = [float(item["raw_frontal_cm"]) - reference for item in items]
        corrected_errors = [float(item["corrected_frontal_cm"]) - reference for item in items]
        summaries.append(
            {
                "measured_cm": reference,
                "capture_count": len(items),
                "raw_metrics": _error_metrics(raw_errors),
                "corrected_metrics": _error_metrics(corrected_errors),
            }
        )
    return summaries
