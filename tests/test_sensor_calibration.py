from services.sensor_calibration import (
    CalibrationProfile,
    build_calibration_profile,
    build_verification_summary,
    validate_calibration_measurements,
)


REFERENCES = (20.0, 60.0, 100.0, 150.0, 200.0)


def _calibration_measurements(samples_per_reference: int = 30) -> list[dict[str, float]]:
    measurements = []
    for reference in REFERENCES:
        for index in range(samples_per_reference):
            sensor_1 = reference * 0.98 - 1.0 + (index % 3) * 0.01
            sensor_2 = reference * 0.985 - 1.2 + (index % 2) * 0.01
            measurements.append(
                {
                    "measured_cm": reference,
                    "sensor_1_cm": sensor_1,
                    "sensor_2_cm": sensor_2,
                    "sensor_cm": (sensor_1 + sensor_2) / 2,
                }
            )
    return measurements


def test_calibration_requires_five_reference_distances() -> None:
    result = validate_calibration_measurements(_calibration_measurements()[:120])
    assert result["validated"] is False
    assert result["status"] == "insufficient_reference_distances"


def test_calibration_requires_thirty_samples_per_reference() -> None:
    result = validate_calibration_measurements(_calibration_measurements(samples_per_reference=29))
    assert result["validated"] is False
    assert result["status"] == "insufficient_samples_per_reference"


def test_calibration_profile_builds_per_sensor_linear_correction() -> None:
    measurements = _calibration_measurements()
    profile_payload = build_calibration_profile(measurements)
    profile = CalibrationProfile.from_dict(profile_payload)

    assert profile.validated is True
    assert profile.correction_ready is True
    assert profile.version.startswith("frontal-distance-v2-")
    assert profile.correct("sensor_1", 97.0) > 97.0
    assert profile_payload["correction_model"]["sensor_1"]["r2"] > 0.999
    assert profile_payload["measurements"] == measurements


def test_verification_requires_new_four_by_thirty_dataset_and_reports_improvement() -> None:
    profile = CalibrationProfile.from_dict(build_calibration_profile(_calibration_measurements()))
    verification = []
    for reference in (40.0, 80.0, 125.0, 175.0):
        for _ in range(30):
            verification.append(
                {
                    "calibration_version": profile.version,
                    "measured_cm": reference,
                    "raw_frontal_cm": reference - 4.0,
                    "corrected_frontal_cm": reference - 0.5,
                }
            )
    summary = build_verification_summary(verification, profile)

    assert summary["verified"] is True
    assert summary["capture_count"] == 120
    assert summary["distinct_reference_count"] == 4
    assert summary["required_reference_distances_cm"] == [40.0, 80.0, 125.0, 175.0]
    assert summary["max_operational_distance_cm"] == 200.0
    assert summary["raw_metrics"]["mae_cm"] == 4.0
    assert summary["corrected_metrics"]["mae_cm"] == 0.5
