from services.sensor_quality import classify_sensor_evidence


def _evidence(samples, **extra):
    return {"enabled": True, "connected": True, "samples": samples, **extra}


def test_quality_classifies_pair_conflict_without_averaging() -> None:
    result = classify_sensor_evidence(
        _evidence(
            {
                "sensor_1": {"distance_cm": 40, "age_ms": 10, "status": "ok"},
                "sensor_2": {"distance_cm": 90, "age_ms": 20, "status": "ok"},
            }
        ),
        max_age_ms=100,
        max_disagreement_cm=15,
    )
    assert result["status"] == "pair_conflict"
    assert "average" not in result


def test_quality_classifies_stale_and_direction_mismatch() -> None:
    stale = classify_sensor_evidence(
        _evidence({"sensor_1": {"distance_cm": 40, "age_ms": 101, "status": "ok"}}),
        max_age_ms=100,
        max_disagreement_cm=15,
    )
    mismatch = classify_sensor_evidence(
        {"status": "camera_sensor_direction_mismatch", "samples": {}}, max_age_ms=100, max_disagreement_cm=15
    )
    assert stale["status"] == "stale"
    assert mismatch["status"] == "direction_mismatch"
