import pytest

from models.sensor_fusion import append_sensor_section, fuse_sensor_reference


def _paired(left=80.0, right=82.0):
    return {
        "status": "paired",
        "samples": {
            "sensor_1": {"distance_cm": left},
            "sensor_2": {"distance_cm": right},
        },
    }


def test_paired_sensor_adds_separate_frontal_reference() -> None:
    contribution = fuse_sensor_reference(_paired(), calibration_validated=False)
    output = append_sensor_section("Terlihat meja. Area tengah relatif dekat.", contribution)
    assert contribution["status"] == "applied"
    assert contribution["frontal_reference_cm"] == 81.0
    assert "Referensi sensor frontal:" in output
    assert contribution["depth_consistency"] == "not_evaluated"


def test_validated_distance_calibration_does_not_claim_object_or_roi_binding() -> None:
    contribution = fuse_sensor_reference(_paired(), calibration_validated=True)
    assert contribution["depth_consistency"] == "distance_reference_validated"
    assert "tidak diikat ke objek atau ROI" in contribution["description"]


def test_pair_conflict_keeps_both_values_and_never_averages() -> None:
    evidence = _paired(40, 90)
    evidence["status"] = "pair_conflict"
    contribution = fuse_sensor_reference(evidence, calibration_validated=True)
    assert contribution["status"] == "conflict"
    assert contribution["frontal_reference_cm"] is None
    assert "40.0 cm" in contribution["description"]
    assert "90.0 cm" in contribution["description"]
    assert "tidak dirata-ratakan" in contribution["description"]


@pytest.mark.parametrize("status", ["partial", "stale", "unavailable", "direction_mismatch"])
def test_invalid_sensor_states_are_insufficient(status) -> None:
    contribution = fuse_sensor_reference({"status": status, "samples": {}}, calibration_validated=False)
    assert contribution["status"] == "insufficient"


def test_sensor_output_does_not_make_prohibited_claims() -> None:
    output = append_sensor_section("Terlihat kursi.", fuse_sensor_reference(_paired(), calibration_validated=True)).lower()
    for prohibited in ("aman dilalui", "jarak objek pasti", "kursi berjarak"):
        assert prohibited not in output
