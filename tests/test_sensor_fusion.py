import pytest

from models.sensor_fusion import append_sensor_section, fuse_sensor_reference
from services.sensor_calibration import CalibrationProfile


def _paired(sensor_1=80.0, sensor_2=82.0):
    return {
        "status": "paired",
        "samples": {
            "sensor_1": {"distance_cm": sensor_1, "age_ms": 5, "status": "ok"},
            "sensor_2": {"distance_cm": sensor_2, "age_ms": 7, "status": "ok"},
        },
    }


def _profile(intercept=0.0, slope=1.0):
    model = {"intercept": intercept, "slope": slope, "r2": 1.0}
    return CalibrationProfile.from_dict({
        "version": "test-v2",
        "status": "validated",
        "validated": True,
        "reference_distances_cm": [20, 60, 100, 150, 200],
        "correction_model": {"sensor_1": model, "sensor_2": model},
    })


def _fuse(evidence, *, calibrated=True, disagreement=15.0, age=1000, profile=None):
    return fuse_sensor_reference(
        evidence,
        calibration_profile=(profile or _profile()) if calibrated else None,
        max_pair_disagreement_cm=disagreement,
        max_age_ms=age,
    )


def test_paired_sensor_uses_arithmetic_mean_as_frontal_reference() -> None:
    contribution = _fuse(_paired())
    output = append_sensor_section("Terlihat meja di tengah ruangan.", contribution)
    assert contribution["status"] == "applied"
    assert contribution["frontal_reference_cm"] == 81.0
    assert contribution["sensor_1_cm"] == 80.0
    assert contribution["sensor_2_cm"] == 82.0
    assert contribution["sensor_1_corrected_cm"] == 80.0
    assert contribution["sensor_2_corrected_cm"] == 82.0
    assert contribution["pair_disagreement_cm"] == 2.0
    assert output.endswith("Referensi jarak frontal sekitar 81.0 cm pada arah sensor.")


def test_reference_is_not_bound_to_named_object() -> None:
    output = append_sensor_section("Terlihat kursi di depan meja.", _fuse(_paired(), calibrated=True)).lower()
    assert "kursi berjarak" not in output
    assert "jarak kursi" not in output


def test_closest_object_is_bound_only_when_pair_is_tightly_consistent() -> None:
    output = append_sensor_section(
        "Sebuah koper hitam terlihat di tengah ruangan.",
        _fuse(_paired(80, 81), disagreement=15.0),
        {"closest_object": "koper hitam"},
    )
    assert "koper hitam tampak sebagai objek paling dekat" in output
    assert "80.5 cm" in output


def test_closest_object_binding_is_withheld_above_two_centimeters() -> None:
    output = append_sensor_section(
        "Sebuah koper hitam terlihat di tengah ruangan.",
        _fuse(_paired(80, 83), disagreement=15.0),
        {"closest_object": "koper hitam"},
    )
    assert "objek paling dekat" not in output
    assert "Referensi jarak frontal" in output
    assert "Referensi jarak frontal" in output


def test_paired_sensor_applies_each_calibration_before_averaging() -> None:
    contribution = _fuse(_paired(80, 82), profile=_profile(intercept=1.0, slope=1.1))
    assert contribution["sensor_1_corrected_cm"] == 89.0
    assert contribution["sensor_2_corrected_cm"] == 91.2
    assert contribution["frontal_reference_cm"] == 90.1


def test_paired_sensor_is_withheld_without_calibration_model() -> None:
    contribution = _fuse(_paired(), calibrated=False)
    assert contribution["status"] == "insufficient"
    assert contribution["reason_code"] == "calibration_not_validated"


def test_pair_conflict_keeps_values_in_provenance_but_not_description() -> None:
    evidence = _paired(40, 90)
    evidence["status"] = "pair_conflict"
    contribution = _fuse(evidence, calibrated=True)
    assert contribution["status"] == "conflict"
    assert contribution["sensor_1_cm"] == 40.0
    assert contribution["sensor_2_cm"] == 90.0
    assert contribution["frontal_reference_cm"] is None
    assert "40.0" not in contribution["description"]
    assert "90.0" not in contribution["description"]


def test_defensive_pair_threshold_withholds_unclassified_disagreement() -> None:
    contribution = _fuse(_paired(60, 90), disagreement=15)
    assert contribution["status"] == "conflict"
    assert contribution["reason_code"] == "sensor_pair_disagreement"
    assert contribution["frontal_reference_cm"] is None


def test_stale_pair_is_withheld() -> None:
    evidence = _paired()
    evidence["samples"]["sensor_2"]["age_ms"] = 2000
    contribution = _fuse(evidence, age=1000)
    assert contribution["status"] == "insufficient"
    assert contribution["reason_code"] == "sensor_sample_stale"


def test_sample_just_after_capture_is_fresh_with_signed_age() -> None:
    evidence = _paired()
    evidence["samples"]["sensor_1"]["age_ms"] = -40
    contribution = _fuse(evidence, age=1000)
    assert contribution["status"] == "applied"
    assert contribution["frontal_reference_cm"] == 81.0


def test_large_negative_age_is_stale() -> None:
    evidence = _paired()
    evidence["samples"]["sensor_1"]["age_ms"] = -2000
    contribution = _fuse(evidence, age=1000)
    assert contribution["status"] == "insufficient"
    assert contribution["reason_code"] == "sensor_sample_stale"


def test_missing_age_is_not_treated_as_fresh() -> None:
    evidence = _paired()
    del evidence["samples"]["sensor_1"]["age_ms"]
    contribution = _fuse(evidence, age=1000)
    assert contribution["status"] == "insufficient"
    assert contribution["reason_code"] == "sensor_sample_stale"


def test_partial_reading_is_labeled_without_average() -> None:
    contribution = _fuse({
        "status": "partial",
        "reason_code": "one_sensor_sample",
        "samples": {"sensor_2": {"distance_cm": 54.0, "age_ms": 4, "status": "ok"}},
    })
    assert contribution["status"] == "partial"
    assert contribution["sensor_1_cm"] is None
    assert contribution["sensor_2_cm"] == 54.0
    assert contribution["frontal_reference_cm"] is None
    assert "Sensor 2 membaca 54.0 cm" in contribution["description"]
    assert "bukan rata-rata" in contribution["description"]


@pytest.mark.parametrize("status", ["stale", "unavailable", "direction_mismatch"])
def test_invalid_sensor_states_are_insufficient(status) -> None:
    contribution = _fuse({"status": status, "samples": {}})
    assert contribution["status"] == "insufficient"
    assert contribution["frontal_reference_cm"] is None
