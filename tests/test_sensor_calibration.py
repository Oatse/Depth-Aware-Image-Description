from services.sensor_calibration import CalibrationProfile, build_calibration_profile, validate_calibration_measurements


def test_calibration_requires_three_measured_targets() -> None:
    result = validate_calibration_measurements([{"measured_cm": 50, "sensor_cm": 51}])
    assert result["validated"] is False
    assert result["status"] == "insufficient_captures"


def test_calibration_profile_version_and_gate() -> None:
    result = validate_calibration_measurements(
        [
            {"measured_cm": 30, "sensor_cm": 31},
            {"measured_cm": 60, "sensor_cm": 59},
            {"measured_cm": 90, "sensor_cm": 91},
        ],
        max_residual_cm=2,
    )
    assert result["validated"] is True
    profile = CalibrationProfile.from_dict({"version": "v1", **result, "sensor_rois": {}})
    assert profile.version == "v1"
    assert profile.validated is True


def test_calibration_requires_three_distinct_reference_distances() -> None:
    result = validate_calibration_measurements(
        [
            {"measured_cm": 60, "sensor_cm": 60},
            {"measured_cm": 60, "sensor_cm": 61},
            {"measured_cm": 60, "sensor_cm": 59},
        ]
    )
    assert result["validated"] is False
    assert result["status"] == "insufficient_reference_distances"


def test_built_profile_preserves_measurement_provenance() -> None:
    measurements = [
        {"measured_cm": 30, "sensor_cm": 31},
        {"measured_cm": 60, "sensor_cm": 59},
        {"measured_cm": 90, "sensor_cm": 91},
    ]
    profile = build_calibration_profile(measurements)
    assert profile["validated"] is True
    assert profile["measurement_kind"] == "frontal_planar_distance"
    assert profile["measurements"] == measurements
